"""Caller-side process outcome; a successful exit is not proof of correct output."""
import subprocess
import sys


def run_python_file(path, timeout=5):
    try:
        result = subprocess.run(
            [sys.executable, str(path)], capture_output=True,
            text=True, encoding="utf-8", timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return {"state": "timeout", "returncode": None,
                "stdout": None, "stderr": None}
    except OSError as exc:
        return {"state": "launch_error", "returncode": None,
                "stdout": None, "stderr": str(exc)}
    except UnicodeError:
        return {"state": "output_encoding_error", "returncode": None,
                "stdout": None, "stderr": "child output is not valid UTF-8"}
    return {"state": "exited_zero" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}
