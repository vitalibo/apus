FROM python:3.9-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --all-packages --no-install-project --no-editable --no-dev

FROM python:3.9-slim

COPY --from=builder --chown=app:app /app/.venv /app/.venv

COPY ./apus-api/src/apus_api/ /app/apus_api
COPY ./apus-shared/src/apus_shared/ /app/apus_shared

ENTRYPOINT ["/app/.venv/bin/python3",  "/app/apus_api/main.py"]
