# Gutendex Docker Setup

Self-hosted [Gutendex](https://github.com/garethbjohnson/gutendex) API for searching Project Gutenberg.

## Prerequisites

You need Docker and Docker Compose installed and running.

### macOS (Homebrew)

If you installed Docker via Homebrew, you need to install the components separately:

```bash
# Install Docker CLI, Compose, and Colima (lightweight Docker runtime)
brew install docker docker-compose colima

# Start the Docker daemon
colima start
```

Stop Colima when you're done with `colima stop`.

### macOS (Docker Desktop)

If you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed, everything is included. Just ensure Docker Desktop is running.

### Linux

Install Docker Engine and the Compose plugin following the [official instructions](https://docs.docker.com/engine/install/).

### Command Syntax Note

The examples below use `docker compose` (with a space). If you installed via Homebrew, use `docker-compose` (with a hyphen) instead.

## Quick Start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set a secure `SECRET_KEY` for production.

3. Start the services and populate the catalog (first run only):
   ```bash
   UPDATE_CATALOG=true docker compose up -d
   ```

4. Subsequent runs (catalog already populated):
   ```bash
   docker compose up -d
   ```

5. Access the API at http://localhost:8000/books/

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | `gutendex` | PostgreSQL password |
| `SECRET_KEY` | (insecure default) | Django secret key - change for production |
| `DEBUG` | `false` | Django debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `GUTENDEX_PORT` | `8000` | Host port to expose |
| `UPDATE_CATALOG` | `false` | Set to `true` to download Gutenberg catalog |

## Usage with textalyzer

Textalyzer is configured to use the local Gutendex instance by default. Once the container is running, use the author search as usual:

```bash
uv run textalyzer-author-search "Jane Austen"
```

If the container isn't running, you'll see a helpful error message with instructions.

To use the public Gutendex API instead, edit `src/textalyzer/config.py`:

```python
GUTENDEX_API_URL = "https://gutendex.com/books/"
```

## Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f gutendex

# Stop services
docker compose down

# Reset everything (including database)
docker compose down -v
```

## Notes

- First run with `UPDATE_CATALOG=true` downloads and imports the Project Gutenberg catalog (~77,000 books). This takes 10-15 minutes depending on your internet connection. The API won't be available until the import completes.
- The catalog data is persisted in a Docker volume, so you only need to run the update once.
- For production, always set a secure `SECRET_KEY` and appropriate `ALLOWED_HOSTS`.
