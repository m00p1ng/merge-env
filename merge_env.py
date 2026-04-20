#!/usr/bin/env python3
"""
merge_env.py — merge .env and JSON files, later files override earlier ones.

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


def parse_env(text: str) -> dict:
    """Parse a .env-style file into a dict."""
    result = {}
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


def parse_json(text: str) -> dict:
    """Parse a JSON file into a flat string dict."""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return {str(k): str(v) for k, v in data.items()}


def detect_and_parse(text: str, hint: str = "") -> dict:
    """Auto-detect format and parse."""
    stripped = text.strip()
    if stripped.startswith("{"):
        return parse_json(text)
    # Try JSON anyway if hinted by extension
    if hint.endswith(".json"):
        return parse_json(text)
    return parse_env(text)


def format_env(data: dict) -> str:
    """Render dict as .env format."""
    lines = []
    for key, value in data.items():
        # Quote values that contain spaces or special characters
        if re.search(r'[\s"\'\\#]', value) or value == "":
            value = '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def format_json(data: dict) -> str:
    """Render dict as pretty JSON."""
    return json.dumps(data, indent=2) + "\n"


def read_source(path: str) -> tuple[str, str]:
    """Return (text, hint) for a path or '-' for stdin."""
    if path == "-":
        return sys.stdin.read(), ""
    p = Path(path)
    return p.read_text(), p.name


def main():
    parser = argparse.ArgumentParser(
        description="Merge .env and JSON files; later files override earlier ones.",
        add_help=False,
    )
    parser.add_argument("files", nargs="*", default=["-"], metavar="FILE",
                        help="Input files (.env or JSON). Use '-' for stdin.")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="Write output to FILE (default: stdout)")
    parser.add_argument("-f", "--format", choices=["env", "json"], default="env",
                        dest="fmt", help="Output format (default: env)")
    parser.add_argument("-h", "--help", action="help",
                        help="Show this help message")

    args = parser.parse_args()

    merged: dict = {}
    stdin_used = False

    for path in args.files:
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

    output = format_json(merged) if args.fmt == "json" else format_env(merged)

    if args.output:
        Path(args.output).write_text(output)
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
