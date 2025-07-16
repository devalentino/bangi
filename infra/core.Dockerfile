FROM python:3.12 AS base

RUN mkdir /app
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml /app
COPY uv.lock /app
COPY Makefile /app
COPY migrations /app/migrations
COPY src /app/src

RUN uv sync --locked

# TODO: start as WSGI
CMD uv run flask --app src/api run --host 0.0.0.0