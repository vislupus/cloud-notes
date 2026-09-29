import os


def normalize_database_url(url: str) -> str:
    """Point plain PostgreSQL URLs at the psycopg (v3) driver.

    Neon and Render hand out URLs such as ``postgres://...`` or
    ``postgresql://...``; SQLAlchemy would otherwise pick psycopg2.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and export it, "
            "or set it in your environment."
        )
    return normalize_database_url(url)
