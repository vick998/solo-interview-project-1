"""Run all validation scripts. Requires HF_TOKEN for QA validation."""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def main() -> int:
    scripts = [
        ("validate_storage.py", "Storage"),
        ("validate_extraction.py", "Extraction"),
        ("validate_qa.py", "QA"),
    ]
    failed = []
    for script, name in scripts:
        if name == "QA" and not os.environ.get("HF_TOKEN", "").strip():
            print(f"SKIP: {name} (HF_TOKEN not set)")
            continue
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / script)],
            cwd=PROJECT_ROOT,
        )
        if result.returncode != 0:
            failed.append(name)
    if failed:
        print(f"\nFailed: {', '.join(failed)}", file=sys.stderr)
        return 1
    print("\nAll validations passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
