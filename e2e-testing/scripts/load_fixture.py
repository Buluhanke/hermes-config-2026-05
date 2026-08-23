#!/usr/bin/env python3
"""
Fixture Loader — load test data from YAML/JSON/ENV files.
Supports {{ key }} and {{ ENV.VAR }} placeholders.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def expand_env(val: str) -> str:
    """Expand {{ ENV.VAR_NAME }} in a string."""
    pattern = r"\{\{\s*ENV\.(\w+)\s*\}\}"
    def replacer(m):
        return os.environ.get(m.group(1), m.group(0))
    return re.sub(pattern, replacer, val)


def expand_dict(obj: Any, fixture: dict = None) -> Any:
    """Recursively expand {{ key }} placeholders in a dict/list/str."""
    if isinstance(obj, dict):
        return {k: expand_dict(v, fixture) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [expand_dict(i, fixture) for i in obj]
    elif isinstance(obj, str):
        # First expand ENV vars
        obj = expand_env(obj)
        # Then expand fixture keys
        if fixture:
            def replacer(m):
                key = m.group(1).strip()
                keys = key.split(".")
                val = fixture
                for k in keys:
                    if isinstance(val, dict):
                        val = val.get(k, m.group(0))
                    else:
                        return m.group(0)
                return str(val)
            obj = re.sub(r"\{\{\s*(.+?)\s*\}\}", replacer, obj)
        return obj
    return obj


def load_fixture(path: str, params: dict = None) -> dict:
    """
    Load a fixture file and expand placeholders.

    Args:
        path: Path to YAML/JSON fixture file
        params: Optional dict to resolve {{ key }} placeholders (overrides file content)
    """
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")

    if p.suffix in (".yaml", ".yml"):
        import yaml
        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    elif p.suffix == ".json":
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    elif p.suffix == ".env":
        # Parse .env file: KEY=value
        data = {}
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip().strip("\"'")
    else:
        raise ValueError(f"Unsupported fixture format: {p.suffix}")

    # If params provided, use them as fixture dict
    if params is not None:
        data = params

    return expand_dict(data)


def dump_fixture(data: dict, path: str = None, fmt: str = None):
    """Save fixture data to a file."""
    if path:
        p = Path(path)
        fmt = fmt or p.suffix.lstrip(".")
    fmt = fmt or "yaml"

    if fmt in ("yaml", "yml"):
        import yaml
        content = yaml.dump(data, allow_unicode=True, default_flow_style=False)
    elif fmt == "json":
        content = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    if path:
        Path(path).write_text(content, encoding="utf-8")
    return content


# CLI
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Load and expand a fixture file")
    parser.add_argument("path", help="Fixture file path")
    parser.add_argument("--param", nargs=2, action="append",
                        metavar=("KEY", "VALUE"),
                        help="Add/override fixture params")
    parser.add_argument("--dump", help="Dump expanded fixture to file")
    args = parser.parse_args()

    params = dict(args.param) if args.param else None
    data = load_fixture(args.path, params)

    print(json.dumps(data, indent=2, ensure_ascii=False))

    if args.dump:
        dump_fixture(data, args.dump)
        print(f"\nSaved to {args.dump}")


if __name__ == "__main__":
    main()
