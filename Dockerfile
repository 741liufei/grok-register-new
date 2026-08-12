# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim AS frontend-builder
WORKDIR /build/front
COPY front/package.json front/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY front/ ./
RUN npm run build

FROM ubuntu:24.04 AS python-builder
ARG DEBIAN_FRONTEND=noninteractive
ARG UBUNTU_MIRROR=http://mirrors.aliyun.com/ubuntu
ARG CAMOUFOX_VERSION=152.0.4
ARG CAMOUFOX_BUILD=beta.28
ARG CAMOUFOX_ASSET_URL=https://github.com/daijro/camoufox/releases/download/v152.0.4-beta.28/camoufox-152.0.4-beta.28-lin.x86_64.zip
ARG CAMOUFOX_ASSET_SHA256=924f3109ccd6d47cd6a0384d67a345fadf975d48b6319f8dbbd5954c588982bd
ARG CAMOUFOX_ASSET_SIZE=663387175
ENV PATH=/opt/venv/bin:$PATH \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    XDG_CACHE_HOME=/opt/camoufox-cache

RUN sed -i \
        -e "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" \
        -e "s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" \
        /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get -o Acquire::Retries=5 update \
    && apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
        ca-certificates python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt ./
RUN python3 -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

# Pin the browser asset and bypass GitHub's rate-limited releases API. The
# installer verifies both size and SHA-256, then launch_path provides a hard
# build failure if the executable is not present.
COPY docker/install_camoufox.py ./docker/install_camoufox.py
RUN python ./docker/install_camoufox.py \
        --version "$CAMOUFOX_VERSION" \
        --build "$CAMOUFOX_BUILD" \
        --url "$CAMOUFOX_ASSET_URL" \
        --sha256 "$CAMOUFOX_ASSET_SHA256" \
        --size "$CAMOUFOX_ASSET_SIZE" \
    && python -m camoufox version

FROM ubuntu:24.04 AS runtime
ARG DEBIAN_FRONTEND=noninteractive
ARG APP_UID=10001
ARG APP_GID=10001
ARG UBUNTU_MIRROR=http://mirrors.aliyun.com/ubuntu

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/app \
    XDG_CACHE_HOME=/opt/camoufox-cache \
    DISPLAY=:99 \
    GROK_WEB_HOST=0.0.0.0 \
    GROK_WEB_PORT=8787 \
    GROK_CONFIG_FILE=/app/data/config.json \
    GROK_FORCE_HEADED=1

# Camoufox/Firefox 有头模式依赖 + Xvfb 虚拟显示器。
RUN sed -i \
        -e "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" \
        -e "s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" \
        /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get -o Acquire::Retries=5 update \
    && apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
        ca-certificates dumb-init gosu procps python3 xvfb xauth \
        libasound2t64 libatk1.0-0t64 libavcodec60 \
        libcairo-gobject2 libcairo2 libdbus-1-3 \
        libfontconfig1 libfreetype6 libgdk-pixbuf-2.0-0 \
        libglib2.0-0t64 libgtk-3-0t64 libpango-1.0-0 \
        libpangocairo-1.0-0 libx11-6 libx11-xcb1 \
        libxcb-shm0 libxcb1 libxcomposite1 libxcursor1 \
        libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 \
        libxrender1 libxtst6 fonts-liberation fonts-noto-color-emoji \
    && groupadd --gid "$APP_GID" app \
    && useradd --uid "$APP_UID" --gid "$APP_GID" --create-home --shell /bin/bash app \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --chown=app:app --from=python-builder /opt/venv /opt/venv
COPY --chown=app:app --from=python-builder /opt/camoufox-cache /opt/camoufox-cache
COPY --chown=app:app backend/ ./backend/
COPY --chown=app:app config.example.json requirements.txt ./
COPY --chown=app:app --from=frontend-builder /build/front/dist ./front/dist/
COPY --chown=app:app --chmod=755 docker/entrypoint.sh ./docker/entrypoint.sh
COPY --chown=app:app docker/camoufox_smoke.py ./docker/camoufox_smoke.py

# Keep the Linux entrypoint executable even when the build context came from a
# Windows checkout with CRLF line endings.
RUN sed -i 's/\r$//' ./docker/entrypoint.sh

RUN install -d -o app -g app /app/data /app/logs

VOLUME ["/app/data", "/app/logs"]
EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/api/health', timeout=3).read()"

ENTRYPOINT ["/usr/bin/dumb-init", "--", "/app/docker/entrypoint.sh"]
CMD ["python", "-m", "backend.web.cli", "--host", "0.0.0.0", "--port", "8787"]
