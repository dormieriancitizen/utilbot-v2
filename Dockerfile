# syntax=docker/dockerfile:1.7-labs

# Use an official Python runtime as the base image
FROM python:3.13.2-alpine3.21 AS base

ENV PYTHONFAULTHANDLER=1 \
PYTHONUNBUFFERED=1 \
PYTHONDONTWRITEBYTECODE=1 \
VIRTUAL_ENV=/opt/venv \
UV_COMPILE_BYTECODE=1 \
UV_LINK_MODE=copy

# Set the working directory in the container
WORKDIR /app

FROM base AS builder-base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN uv venv $VIRTUAL_ENV
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

FROM base AS production
RUN apk add --no-cache ffmpeg
COPY --from=builder-base /opt/venv /opt/venv
COPY . .

# Specify the command to run your project
CMD [ "python3", "main.py"]
