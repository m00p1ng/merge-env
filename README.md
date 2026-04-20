# merge-env

A lightweight CLI tool to merge multiple `.env` and JSON configuration files into a single environment representation. Later files override earlier ones, making it ideal for layered configuration workflows in scripts and CI/CD pipelines.

## Features

- **Multi-format support**: Merge `.env` files and JSON files seamlessly
- **Auto-detection**: Automatically detects file format (with optional hints)
- **Override behavior**: Later files override values from earlier files
- **Flexible input**: Read from files or stdin
- **Multiple output formats**: Output as `.env` or pretty-printed JSON
- **Proper escaping**: Handles quotes, spaces, and special characters in values
- **Comprehensive tests**: Full test suite with 30+ test cases

## Installation

### From source

Clone the repository and install:

```bash
git clone https://github.com/m00p1ng/merge-env.git
cd merge-env
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

### Basic syntax

```bash
merge_env.py [OPTIONS] [FILE...]
```

### Command-line options

```
  FILE                  Input files (.env or JSON). Use '-' for stdin.
  -o, --output FILE     Write output to FILE (default: stdout)
  -f, --format FORMAT   Output format: env (default) or json
  -h, --help            Show this help message
```

### Examples

#### Merge two `.env` files (second overrides first)

```bash
merge_env.py config.env secrets.env
```

#### Merge `.env` and JSON files

```bash
merge_env.py defaults.env overrides.json
```

#### Read from stdin

```bash
cat config.env | merge_env.py -
```

#### Chain multiple files with stdin

```bash
cat base.env | merge_env.py - overrides.env
```

#### Output as JSON

```bash
merge_env.py --format json config.env secrets.json
```

#### Save output to a file

```bash
merge_env.py -o merged.env config.env secrets.env
```

#### Output JSON to a file

```bash
merge_env.py --format json -o merged.json config.env secrets.json
```

### File format details

#### `.env` format

Standard dotenv format with support for:
- Key-value pairs: `KEY=value`
- Quoted values: `KEY="value with spaces"`
- Comments: Lines starting with `#`
- Empty values: `KEY=`

Example:
```bash
DATABASE_URL=postgres://localhost/mydb
API_KEY="my-secret-key"
DEBUG=true
# This is a comment
EMPTY_VAR=
```

#### JSON format

Flat JSON object with string values:
```json
{
  "DATABASE_URL": "postgres://localhost/mydb",
  "API_KEY": "my-secret-key",
  "DEBUG": "true"
}
```

### Merge behavior

- Files are merged in order (left to right)
- Later files override values from earlier files
- All values are stored as strings
- The final output format is determined by the `--format` flag

Example:
```bash
# config.env
DATABASE_URL=postgres://localhost/dev
DEBUG=false

# secrets.env
DATABASE_URL=postgres://prod-server/db
API_KEY=super-secret

# Merge command
merge_env.py config.env secrets.env
```

Output:
```
DATABASE_URL=postgres://prod-server/db
DEBUG=false
API_KEY=super-secret
```

## Development

### Run tests

```bash
pytest
```

### Run with verbose output

```bash
pytest -v
```

### Run specific test class

```bash
pytest test_merge_env.py::TestParseEnv -v
```

## License

MIT
