---
title: "Installation"
description: "Install Vex via binary download, Homebrew, Docker, or from source."
category: "Getting Started"
order: 2
tags: [install, setup, docker, homebrew]
---

# Installation

Vex ships as a single statically-linked binary with no external runtime dependencies. Pick whichever method suits your environment.

## Binary download

Download the latest release for your platform from [GitHub Releases](https://github.com/example/vex/releases):

```bash
# macOS (Apple Silicon)
curl -Lo vex https://github.com/example/vex/releases/latest/download/vex_darwin_arm64
chmod +x vex && sudo mv vex /usr/local/bin/

# Linux (amd64)
curl -Lo vex https://github.com/example/vex/releases/latest/download/vex_linux_amd64
chmod +x vex && sudo mv vex /usr/local/bin/
```

Verify the installation:

```bash
vex --version
# vex 1.4.2
```

## Homebrew (macOS / Linux)

```bash
brew tap example/vex
brew install vex
```

## Docker

```bash
docker pull ghcr.io/example/vex:latest

docker run -d \
  --name vex \
  -p 8000:8000 \
  -p 8001:8001 \
  -v $(pwd)/vex.yaml:/etc/vex/vex.yaml \
  ghcr.io/example/vex:latest
```

Port `8000` is the proxy (traffic) port. Port `8001` is the Admin API.

## Docker Compose

```yaml
services:
  vex:
    image: ghcr.io/example/vex:latest
    ports:
      - "8000:8000"   # proxy
      - "8001:8001"   # admin API
    volumes:
      - ./vex.yaml:/etc/vex/vex.yaml
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
```

## From source

Requires Go 1.22+:

```bash
git clone https://github.com/example/vex.git
cd vex
make build
sudo mv ./bin/vex /usr/local/bin/
```

## System requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 1 core | 2+ cores |
| Memory | 64 MB | 256 MB |
| OS | Linux, macOS, Windows (WSL2) | Linux |

## Next steps

- [Quick Start](./quickstart.md) — proxy your first request
- [Configuration Reference](./configuration.md) — full YAML schema
