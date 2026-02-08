# Phanthand

[![日本語](https://img.shields.io/badge/lang-日本語-blue)](README.ja.md)

Lightweight file access API server for development PCs. Designed for AI-assisted development workflows where an AI agent on a remote server needs read-only access to source files on your local machine.

## Features

- **Read-only file access** — Read files, list directories, search by glob patterns
- **Path whitelist security** — Only explicitly allowed directories are accessible
- **Bearer token authentication** — Simple API key protection
- **Zero config deployment** — Single YAML config file, no database required

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setup

```bash
git clone https://github.com/SpirrowGames/spirrow-phanthand.git
cd spirrow-phanthand

# Create config from example
cp config.example.yaml config.yaml
# Edit config.yaml — set your API key and allowed paths
```

### Run

```bash
# With uv (recommended)
uv run phanthand

# With pip
pip install -e .
python -m phanthand
```

## Configuration

Edit `config.yaml`:

```yaml
server:
  host: "0.0.0.0"    # Listen address
  port: 7300          # Listen port

security:
  api_key: "your-secret-key"    # Bearer token
  allowed_paths:                 # Whitelisted directories
    - "D:/Projects"
    - "C:/Dev/my-project"
  max_file_size_mb: 10           # Max file size for reads
```

> **Note:** `config.yaml` is gitignored. Only `config.example.yaml` is tracked.

## API Endpoints

### System

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |

### File Operations

All file endpoints require `Authorization: Bearer <api_key>` header.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/files/read` | Read a text file |
| POST | `/files/list` | List directory contents |
| POST | `/files/exists` | Check file/directory existence |
| POST | `/files/info` | Get file metadata |
| POST | `/files/tree` | Recursive directory tree |
| POST | `/files/search` | Glob pattern search |

### Example

```bash
# Health check
curl http://localhost:7300/health

# Read a file
curl -X POST http://localhost:7300/files/read \
  -H "Authorization: Bearer your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"path": "D:/Projects/my-app/src/main.py"}'
```

### Response Format

All responses follow a consistent format:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

## Security

- All file operations are restricted to paths listed in `allowed_paths`
- Symlink traversal is prevented by resolving paths before validation
- File reads are capped at `max_file_size_mb`
- No write operations are supported

## License

MIT License — see [LICENSE](LICENSE) for details.
