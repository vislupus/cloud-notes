# CLAUDE.md

Development notes for Cloud Notes, a FastAPI + PostgreSQL notes app with
server-rendered Jinja2 pages.

## Layout

- `app/config.py` – reads `DATABASE_URL` and normalizes it to the
  `postgresql+psycopg://` driver.
- `app/database.py` – SQLAlchemy engine, `SessionLocal`, `Base`, `get_db`
  dependency. The engine is created at import time from `DATABASE_URL`.
- `app/models.py` – the `Note` model (`id`, `title`, `content`, `created_at`,
  `updated_at`; timestamps are timezone-aware UTC).
- `app/main.py` – all routes. Tables are created with
  `Base.metadata.create_all` in the app lifespan (no migrations yet).
- `app/templates/` – Jinja2 templates (`base.html`, `index.html`,
  `note_form.html`).
- `app/static/style.css` – all styling; responsive, light/dark via
  `prefers-color-scheme`.
- `tests/` – pytest suite using FastAPI's `TestClient`.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

pytest                                   # in-memory SQLite
TEST_DATABASE_URL=postgresql://... pytest  # against a throwaway Postgres DB

DATABASE_URL=postgresql://... uvicorn app.main:app --reload
```

## Conventions

- No JavaScript. Forms use plain `POST`; updates go to `POST /notes/{id}` and
  deletes to `POST /notes/{id}/delete`, each redirecting with `303`.
- Validation errors re-render the form with status `422`.
- Keep runtime dependencies in `requirements.txt` (pinned) and test-only
  dependencies in `requirements-dev.txt`.
- Reference static files with root-relative paths (`/static/...`), not
  `url_for`, so pages work behind Render's TLS proxy.
- `tests/conftest.py` sets `DATABASE_URL` before importing the app; keep that
  ordering. Tests must pass on both SQLite and PostgreSQL.
- Add or update tests for every behavior change and run `pytest` before
  committing.

## Secrets

- Never commit secrets or credentials. `DATABASE_URL` comes from the
  environment: a git-ignored `.env` locally, and the Render dashboard in
  production (`sync: false` in `render.yaml`).
- `.env.example` must contain placeholders only.

## Deployment

- Production database: PostgreSQL on Neon (connection string must include
  `sslmode=require`).
- Hosting: Render (Frankfurt region, near the EU Neon database), Docker
  runtime, defined in `render.yaml`. Health check path
  is `/health`, which pings the database.
