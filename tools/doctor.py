"""Read-only local prerequisites diagnostic; makes no network calls or purchases."""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import json


def diagnose() -> dict:
    return {
        "python": sys.version.split()[0],
        "python_supported": sys.version_info >= (3, 11),
        "docker_cli_available": shutil.which("docker") is not None,
        "inference_key_configured": bool(os.getenv("VULTR_INFERENCE_API_KEY")),
        "openai_sdk_installed": importlib.util.find_spec("openai") is not None,
        "fastapi_installed": importlib.util.find_spec("fastapi") is not None,
        "note": "No Docker containers, Vultr calls, network requests or infrastructure changes were made."
    }

if __name__ == "__main__":
    print(json.dumps(diagnose(), indent=2))
