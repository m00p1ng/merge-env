#!/usr/bin/env python3
"""
merge_env.py - merge .env and JSON files, later files override earlier ones.

Usage:
  merge_env.py [OPTIONS] [FILE...]

  Files can be .env or JSON format. Use '-' to read from stdin.
  If no files are given, reads from stdin.

Options:
  -o, --output FILE    Write output to FILE instead of stdout
  -f, --format FORMAT  Output format: env (default) or json
  -h, --help           Show this help message
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import cast


def parse_env(text: str) -> dict[str, str]:
    """Parse a .env-style file into a dict."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip optional surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def parse_json(text: str) -> dict[str, str]:
    """Parse a JSON file into a flat string dict."""
    # json.loads returns an untyped value; check it at runtime and use it if it's a dict.
    obj = cast(object, json.loads(text))
    if not isinstance(obj, dict):
        raise ValueError("JSON root must be an object")
    data = cast(dict[str, object], obj)
    return {str(k): str(v) for k, v in data.items()}


def detect_and_parse(text: str, hint: str = "") -> dict[str, str]:
    """Auto-detect format and parse."""
    stripped = text.strip()
    if stripped.startswith("{"):
        return parse_json(text)
    # Try JSON anyway if hinted by extension
    if hint.endswith(".json"):
        return parse_json(text)
    return parse_env(text)


def format_env(data: dict[str, str]) -> str:
    """Render dict as .env format."""
    lines: list[str] = []
    for key, value in data.items():
        # Quote values that contain spaces or special characters
        if re.search(r'[\s"\'\\#]', value) or value == "":
            value = '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def format_json(data: dict[str, str]) -> str:
    """Render dict as pretty JSON."""
    return json.dumps(data, indent=2) + "\n"


def read_source(path: str) -> tuple[str, str]:
    """Return (text, hint) for a path or '-' for stdin."""
    if path == "-":
        return sys.stdin.read(), ""
    p = Path(path)
    return p.read_text(), p.name


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge .env and JSON files; later files override earlier ones.",
        add_help=False,
    )
    _ = parser.add_argument(
        "files",
        nargs="*",
        default=["-"],
        metavar="FILE",
        help="Input files (.env or JSON). Use '-' for stdin.",
    )
    _ = parser.add_argument(
        "-o", "--output", metavar="FILE", help="Write output to FILE (default: stdout)"
    )
    _ = parser.add_argument(
        "-f",
        "--format",
        choices=["env", "json"],
        default="env",
        dest="fmt",
        help="Output format (default: env)",
    )
    _ = parser.add_argument(
        "-h", "--help", action="help", help="Show this help message"
    )

    args = parser.parse_args()
    # Pull typed locals from the (dynamically-typed) Namespace to satisfy the type checker
    files: list[str] = cast(list[str], args.files)
    output_arg: str | None = cast(str | None, args.output)
    fmt: str = cast(str, args.fmt)

    merged: dict[str, str] = {}
    stdin_used: bool = False

    if output_arg:
        output_path = Path(output_arg)
        if output_path.exists():
            try:
                text = output_path.read_text()
                merged.update(detect_and_parse(text, output_path.name))
            except (OSError, json.JSONDecodeError, ValueError):
                pass

    for path in files:
        if path == "-":
            if stdin_used:
                parser.error("stdin ('-') can only be used once")
            stdin_used = True

        try:
            text, hint = read_source(path)
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)

        try:
            data = detect_and_parse(text, hint)
        except (json.JSONDecodeError, ValueError) as e:
            label = "stdin" if path == "-" else path
            print(f"error: could not parse {label}: {e}", file=sys.stderr)
            sys.exit(1)

        merged.update(data)

    output = format_json(merged) if fmt == "json" else format_env(merged)

    if output_arg:
        _ = Path(output_arg).write_text(output)
    else:
        _ = sys.stdout.write(output)


if __name__ == "__main__":
    main()
