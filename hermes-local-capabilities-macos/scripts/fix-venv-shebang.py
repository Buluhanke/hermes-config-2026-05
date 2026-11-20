#!/usr/bin/env python3
"""Fix venv shebang path typo in hermes-agent executables.

The installer incorrectly generates shebang with `.venv2/` instead of `.venv/`.
This script corrects all three executables at once.

Usage:
    python3 fix-venv-shebang.py
"""

import os

for f in ['hermes', 'hermes-agent', 'hermes-acp']:
    path = os.path.expanduser('~/.hermes/hermes-agent/.venv/bin/' + f)
    try:
        with open(path, 'r') as file:
            content = file.read()
        new_content = content.replace('.venv2/', '.venv/')
        with open(path, 'w') as file:
            file.write(new_content)
        print(f"fixed {path}")
    except FileNotFoundError:
        print(f"not found: {path}")
    except Exception as e:
        print(f"error on {path}: {e}")

print("Done.")