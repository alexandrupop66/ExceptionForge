from pathlib import Path
import pytest
from app.sandbox import SandboxError, build_docker_command, validate_code


def test_minimum_security_flags():
    cmd = build_docker_command(Path("/tmp/ef-code.py"), Path("/tmp/ef-data"), "ef-test")
    expected = ["--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "64", "--memory", "256m", "--memory-swap", "256m", "--cpus", "0.5", "--user", "65534:65534"]
    for entry in expected:
        assert entry in cmd
    assert "--privileged" not in cmd
    assert "-v" not in cmd


def test_generated_code_forbids_network_import():
    with pytest.raises(SandboxError, match="disallowed module"):
        validate_code("import socket\nprint('hello')")


def test_generated_code_forbids_dynamic_exec():
    with pytest.raises(SandboxError, match="disallowed function"):
        validate_code("exec('print(1)')")


def test_valid_generated_python():
    validate_code('import csv\nimport json\nprint(json.dumps({"findings": [], "analysed_invoices": 1}))')
