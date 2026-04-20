merge-env
=========

merge-env is a small CLI tool to merge dotenv-style files (.env) and JSON files into a single environment representation. Later files override earlier ones. It is intended for simple environment merging workflows in scripts and CI.

Features
- Merge multiple .env and JSON files (later files override earlier values)
- Read from stdin when `-` is provided or no files are given
- Output as dotenv or JSON

Installation

Clone the repository and (optionally) create a virtual environment:

```bash
git clone https://github.com/m00p1ng/merge-env.git
cd merge-env
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Usage

Basic usage (merge two files, second overrides first):

```bash
merge_env file1.env file2.json
```

Read from stdin (use `-`):

```bash
cat file.env | merge_env -
```

Output as JSON:

```bash
merge_env --json file1.env file2.json
```

Run tests

```bash
pytest
```

License

MIT
