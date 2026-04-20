# merge-env

A lightweight command-line utility for merging `.env` and JSON configuration files with support for multiple input formats and flexible output options.

## Features

- **Multi-format support**: Parse `.env` files and JSON configurations
- **Automatic format detection**: Intelligently detect file format based on content or extension
- **File merging**: Combine multiple configuration sources with later files overriding earlier ones
- **Flexible I/O**: Read from files or stdin, write to stdout or file
- **Multiple output formats**: Export as `.env` format or JSON
- **Zero dependencies**: No external runtime dependencies
- **Well-tested**: Comprehensive test suite with 47+ tests

## Installation

### Requirements
- Python 3.12+
- `uv` package manager (optional, but recommended)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd merge-env

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (development)
uv pip install -e ".[dev]"
# or with pip
pip install pytest
```

## Usage

### Basic Merging

Merge multiple configuration files with later files overriding earlier ones:

```bash
./merge_env.py base.env local.env > merged.env
```

### Format Detection

The utility automatically detects file formats (`.env` or JSON):

```bash
# Merge .env and JSON files
./merge_env.py config.env settings.json

# Explicitly specify output format
./merge_env.py config.env settings.json -f json
```

### Output to File

```bash
./merge_env.py config.env local.env -o .env.production
```

### Using stdin

Read configuration from stdin:

```bash
echo "KEY=value" | ./merge_env.py - config.env
cat base.env | ./merge_env.py - local.json
```

### Output Formats

**Default (`.env` format)**:
```bash
./merge_env.py config.env
# Output:
# DATABASE_URL=postgresql://localhost/db
# API_KEY=secret123
```

**JSON format**:
```bash
./merge_env.py config.env -f json
# Output:
# {
#   "DATABASE_URL": "postgresql://localhost/db",
#   "API_KEY": "secret123"
# }
```

## Command-line Options

```
Usage: merge_env.py [OPTIONS] [FILE...]

Arguments:
  FILE                 Configuration files to merge (use - for stdin)

Options:
  -o, --output FILE    Write output to FILE instead of stdout
  -f, --format FORMAT  Output format: env (default) or json
  -h, --help           Show this help message and exit
```

## Examples

### Example 1: Development and Production Configs

Merge a base configuration with environment-specific overrides:

```bash
# Base configuration (config.env)
DATABASE_URL=sqlite:///:memory:
DEBUG=false
LOG_LEVEL=info

# Production overrides (prod.env)
DATABASE_URL=postgresql://prod-db:5432/app
DEBUG=false
LOG_LEVEL=warning

# Merge them
./merge_env.py config.env prod.env -o .env.production
```

### Example 2: Multi-source Configuration

Combine settings from multiple sources:

```bash
./merge_env.py defaults.json secrets.json local-overrides.env -f json
```

### Example 3: CI/CD Pipeline

Build configuration dynamically in a pipeline:

```bash
# Start with defaults
cat defaults.env > .env

# Apply environment-specific config
./merge_env.py .env config.$ENVIRONMENT.env -o .env

# Override with secrets (if available)
if [ -f secrets.env ]; then
  ./merge_env.py .env secrets.env -o .env
fi
```

## File Formats

### `.env` Format

Standard key=value pairs, one per line:

```env
# Comments are supported
DATABASE_URL=postgresql://localhost/db
API_KEY=secret123
DEBUG=true

# Empty values are supported
OPTIONAL_SETTING=

# Values with spaces or special characters are quoted
LONG_VALUE="This is a long value with spaces"
```

### JSON Format

Standard JSON object with string values:

```json
{
  "DATABASE_URL": "postgresql://localhost/db",
  "API_KEY": "secret123",
  "DEBUG": "true"
}
```

Note: JSON arrays and primitives are not supported; the root must be an object.

## Behavior

- **Override Strategy**: Later files override values from earlier files (last-write-wins)
- **Type Coercion**: All values are stored and output as strings
- **Escaping**: Special characters (quotes, backslashes) are properly escaped in `.env` output
- **Comments**: Comments in `.env` files are stripped during parsing
- **Whitespace**: Leading/trailing whitespace around keys is trimmed

