FROM python:3.12-slim

# Pin uv CLI image for reproducible dependency installation
COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /uvx /bin/

WORKDIR /app

# Install frozen dependencies first so code edits reuse Docker layer cache
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source and install the project package cleanly
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY data ./data
COPY frontend ./frontend
COPY scripts ./scripts
COPY .streamlit ./.streamlit
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m scripts.seed && python -m scripts.ingest && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
