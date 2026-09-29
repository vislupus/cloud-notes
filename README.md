# cloud-notes

Simple cloud notes app built with Python, FastAPI and PostgreSQL.

Create, list, edit and delete notes from a responsive, server-rendered
HTML interface (Jinja2 templates, plain CSS, no JavaScript). Each note has an
`id`, `title`, `content`, `created_at` and `updated_at`.

## Stack

- Python 3.11+ / FastAPI
- SQLAlchemy 2 with the psycopg 3 driver
- PostgreSQL ([Neon](https://neon.tech) in production)
- Jinja2 templates + plain CSS
- Deployed on [Render](https://render.com) via Docker

## Running locally

1. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```

2. Configure the database. Copy `.env.example` to `.env`, set `DATABASE_URL`
   to a PostgreSQL database (local or Neon), and export it:

   ```bash
   cp .env.example .env
   set -a; source .env; set +a
   ```

   `postgres://` and `postgresql://` URLs are accepted and automatically use
   the psycopg 3 driver. The `notes` table is created on startup.

3. Start the server:

   ```bash
   uvicorn app.main:app --reload
   ```

   Open http://localhost:8000.

## Routes

| Method | Path                  | Description                  |
| ------ | --------------------- | ---------------------------- |
| GET    | `/`                   | List all notes               |
| GET    | `/notes/new`          | New note form                |
| POST   | `/notes`              | Create a note                |
| GET    | `/notes/{id}/edit`    | Edit note form               |
| POST   | `/notes/{id}`         | Update a note                |
| POST   | `/notes/{id}/delete`  | Delete a note                |
| GET    | `/health`             | Health check (includes a DB ping; 503 if the DB is unreachable) |

## Tests

```bash
pytest
```

By default the tests use in-memory SQLite, so no database is needed. To run
them against PostgreSQL, point `TEST_DATABASE_URL` at a **dedicated, empty**
test database (tables are dropped after every test):

```bash
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cloud_notes_test pytest
```

GitHub Actions runs the suite against PostgreSQL 16 on every pull request
(`.github/workflows/tests.yml`).

## Docker

```bash
docker build -t cloud-notes .
docker run --rm -p 8000:8000 -e DATABASE_URL="postgresql://..." cloud-notes
```

The container listens on `$PORT` (default `8000`).

## Deploying to Render + Neon

1. Create a Neon project and copy its connection string
   (`postgresql://USER:PASSWORD@HOST.neon.tech/DBNAME?sslmode=require`).
2. In Render, create a new **Blueprint** from this repository. `render.yaml`
   defines a Docker web service with `/health` as its health check.
3. When prompted, set `DATABASE_URL` to the Neon connection string. It is
   declared with `sync: false`, so the value lives only in Render and never in
   the repository.

## Configuration

| Variable       | Required | Description                        |
| -------------- | -------- | ---------------------------------- |
| `DATABASE_URL` | yes      | PostgreSQL connection string       |
| `PORT`         | no       | Port for the Docker container (Render sets this) |

Never commit `.env` or real credentials; `.env` is git-ignored.
