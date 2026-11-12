# Node is needed by yt-dlp to solve YouTube's JS challenges
FROM node:22-slim AS node

FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git ffmpeg build-essential libffi-dev libssl-dev ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=node /usr/local/bin/node /usr/local/bin/node

WORKDIR /app

COPY requirements.txt .
RUN pip install -U pip setuptools wheel \
    && pip install -r requirements.txt

COPY . .

CMD ["bash", "start"]
