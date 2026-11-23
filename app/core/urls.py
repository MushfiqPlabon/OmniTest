"""Database connection URL normalization helper.

Why this exists:
Hosted PostgreSQL services (like Render or Railway) provide URLs starting with
`postgres://` or containing `sslmode=require`, which work with synchronous
`psycopg2` but fail with async `asyncpg`. `normalize_async_database_url` rewrites
those safely using SQLAlchemy's `make_url` parser.
"""

from sqlalchemy.engine import make_url


def normalize_async_database_url(url: str) -> str:
    """Ensure Render/cloud postgres URLs use postgresql+asyncpg and asyncpg-compatible ssl params."""
    parsed = make_url(url.strip())
    if parsed.drivername in ("postgres", "postgresql"):
        parsed = parsed.set(drivername="postgresql+asyncpg")

    # asyncpg rejects psycopg2's `sslmode` query key, so rename it to `ssl`.
    if "sslmode" in parsed.query:
        clean_query = {}
        for key, value in parsed.query.items():
            target_key = "ssl" if key == "sslmode" else key
            clean_query[target_key] = value
        parsed = parsed.set(query=clean_query)

    # CRITICAL: str(parsed) masks passwords as '***', so pass hide_password=False.
    return parsed.render_as_string(hide_password=False)
