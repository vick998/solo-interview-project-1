---
name: Phase 1 Project Scaffold
overview: Set up the minimal FastAPI project scaffold with app structure, config, dependencies, and a health endpoint as specified in Phase 1 of the development plan.
todos: []
isProject: false
---

# Phase 1: Project Scaffold

## Current State

The project is empty except for `DEVELOPMENT_PLAN.md`, `README.md`, `.gitignore`, and the tech assignment docs. No `app/` directory or `pyproject.toml` exists yet. We will use **uv** for dependency management and virtual environment (cleaner, faster than pip/venv).

## Implementation Steps

### 1. Create `app/` package structure

- Create [app/](app/) directory
- Add [app/**init**.py](app/__init__.py) (can be empty or minimal)

### 2. Create minimal FastAPI app with health route

- Create [app/main.py](app/main.py)
- Instantiate FastAPI app
- Add `GET /health` route that returns JSON, e.g. `{"status": "ok"}`
- Use `@app.get("/health")` decorator

### 3. Create config module

- Create [app/config.py](app/config.py)
- Define settings for `UPLOAD_DIR` (e.g. `./uploads` or `tempfile.gettempdir()`)
- Define `SESSION_TIMEOUT` (e.g. seconds or timedelta)
- Use simple module-level constants or a small config class; no need for Pydantic Settings yet

### 4. Set up uv and dependencies

- Run `uv init` to create [pyproject.toml](pyproject.toml) and `.venv` (or `uv sync` after manual pyproject.toml creation)
- Add Phase 1 dependencies with uv: `uv add fastapi "uvicorn[standard]" python-multipart`
- This creates/updates `pyproject.toml` and `uv.lock`; `.venv` is auto-created and already in `.gitignore`
- Optional: keep [requirements.txt](requirements.txt) for Docker/CI compatibility via `uv export --no-dev -o requirements.txt` (can be added in Phase 6)

### 5. Validation

After implementation:

- Start server: `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (uv auto-activates `.venv`)
- Verify: `curl -s http://localhost:8000/health | jq .` returns 200 and JSON like `{"status": "ok"}`

## Success Criteria (from plan)

- No import or startup errors
- `GET /health` returns 200 with JSON body

## File Summary


| File              | Purpose                                    |
| ----------------- | ------------------------------------------ |
| `app/__init__.py` | Package marker                             |
| `app/main.py`     | FastAPI app + `/health` route              |
| `app/config.py`   | `UPLOAD_DIR`, `SESSION_TIMEOUT`            |
| `pyproject.toml`  | Project metadata + dependencies (uv)       |
| `uv.lock`         | Locked dependency versions (commit to git) |


## Notes

- **Prerequisite:** uv must be installed (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`)
- Use `uv run` for all commands (uv auto-uses `.venv`); no manual `source .venv/bin/activate` needed
- `uv add <pkg>` adds to `pyproject.toml` and installs; `uv sync` installs from lockfile
- The `app/config.py` values will be used in later phases (Phase 2 for uploads, Phase 3 for sessions)

