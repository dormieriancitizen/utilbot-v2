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
RUN apk add --no-cache git
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY uv.lock pyproject.toml /app

RUN uv venv $VIRTUAL_ENV
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY . /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

FROM base AS production
RUN apk add --no-cache ffmpeg
COPY --from=builder-base /opt/venv /opt/venv

# Specify the command to run your project
CMD [ "python3", "main.py"]
