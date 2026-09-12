FROM mcr.microsoft.com/devcontainers/python:3-3.14-trixie

ENV PYTHONUNBUFFERED 1

RUN mkdir -p /home/vscode/.vscode-server && chown -R vscode:vscode /home/vscode/.vscode-server*

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

USER vscode