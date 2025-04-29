# syntax=docker/dockerfile:1.7-labs

# Use an official Python runtime as the base image
FROM python:3-alpine AS base

ENV PYTHONFAULTHANDLER=1 \
PYTHONUNBUFFERED=1 \
PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

FROM base AS builder-base
RUN apk add --no-cache git

COPY requirements.txt ./
RUN pip install -r requirements.txt

FROM base AS production
RUN apk add --no-cache ffmpeg
COPY --from=builder-base --parents /usr/local/lib/python*/site-packages/ /
COPY . .

# Specify the command to run your project
CMD [ "python3", "main.py"]
