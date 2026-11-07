"""Launch model-authored Python in a disposable, constrained Docker container.

IMPORTANT: a Docker container alone is not a proof of complete host isolation.
Do not run this service with a publicly exposed Docker socket. No fallback to
executing generated code on the host is ever permitted.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

IMAGE = "python:3.12-alpine"
MAX_STDOUT = 200_000
MAX_CODE = 24_000
ALLOWED_IMPORTS = frozenset({"csv", "json", "collections", "decimal", "math", "re", "itertools", "statistics", "datetime"})


class SandboxError(RuntimeError):
    pass


def validate_code(code: str) -> None:
    """Defence-in-depth filter, NOT a replacement for the Docker boundary."""
    if len(code.encode("utf-8")) > MAX_CODE:
        raise SandboxError("Generated program exceeds size limit")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise SandboxError(f"Syntax error: {exc.msg} at line {exc.lineno}") from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
            if any(name not in ALLOWED_IMPORTS for name in names):
                raise SandboxError("Generated code requests a disallowed module")
        elif isinstance(node, ast.ImportFrom):
            if not node.module or node.module.split(".")[0] not in ALLOWED_IMPORTS:
                raise SandboxError("Generated code requests a disallowed module")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "compile", "__import__", "input", "breakpoint"}:
            raise SandboxError("Generated code requests a disallowed function")
    if "__" in code:
        raise SandboxError("Dunder access is not permitted in generated code")


def build_docker_command(code_path: Path, data_dir: Path, container_name: str) -> list[str]:
    return [
        "docker", "run", "--rm", "--name", container_name,
        "--network", "none", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--pids-limit", "64",
        "--memory", "256m", "--memory-swap", "256m", "--cpus", "0.5",
        "--user", "65534:65534", "--tmpfs", "/tmp:rw,nosuid,noexec,size=32m",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        "--mount", f"type=bind,src={code_path.resolve()},dst=/work/run.py,readonly",
        "--mount", f"type=bind,src={data_dir.resolve()},dst=/data,readonly",
        "--workdir", "/work", "--entrypoint", "python", IMAGE, "/work/run.py",
    ]


def run_isolated(code: str, data_dir: Path, *, validate: bool = True, timeout: int = 12) -> dict:
    if validate:
        validate_code(code)
    if not data_dir.is_dir():
        raise SandboxError("Dataset directory missing")
    with tempfile.TemporaryDirectory(prefix="exceptionforge-code-") as tmp:
        script = Path(tmp) / "run.py"
        script.write_text(code, encoding="utf-8")
        script.chmod(0o644)
        Path(tmp).chmod(0o755)  # Container non-root must traverse directory.
        name = "exceptionforge-" + uuid.uuid4().hex[:12]
        cmd = build_docker_command(script, data_dir, name)
        try:
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False, env={"PATH": os.getenv("PATH", "")})
        except FileNotFoundError as exc:
            raise SandboxError("Docker is unavailable; generated code was NOT run") from exc
        except subprocess.TimeoutExpired as exc:
            raise SandboxError("Sandbox timed out; container was terminated") from exc
        finally:
            # A timed-out docker CLI may leave a container behind; always try cleanup.
            try:
                subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=4, check=False)
            except (OSError, subprocess.TimeoutExpired):
                pass
        output = completed.stdout[:MAX_STDOUT]
        stderr = completed.stderr[:4000]
        return {"exit_code": completed.returncode, "stdout": output, "stderr": stderr, "sandbox": {"network": "none", "read_only_root": True, "capabilities": "dropped", "memory_mb": 256, "pids": 64, "cpu": 0.5, "docker_invoked": True}}


def containment_probe(data_dir: Path) -> dict:
    """Fixed synthetic test; intentionally attempts egress inside the same sandbox path.

    No real invoice data or secrets are sent, and the IP is documentation-only.
    """
    code = '''import json
import socket
try:
    s = socket.socket()
    s.settimeout(2)
    s.connect(("192.0.2.1", 443))
    print(json.dumps({"network_probe": "UNEXPECTED_CONNECTED"}))
except OSError as error:
    print(json.dumps({"network_probe": "BLOCKED", "kernel_error": str(error)}))
'''
    result = run_isolated(code, data_dir, validate=False, timeout=10)
    try:
        probe = json.loads(result["stdout"].strip())
    except (ValueError, TypeError):
        probe = {"network_probe": "INDETERMINATE"}
    return {**result, "probe": probe, "passed": result["exit_code"] == 0 and probe.get("network_probe") == "BLOCKED"}
