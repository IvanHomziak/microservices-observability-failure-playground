#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[stop-local] Stopping docker compose services..."
docker compose down

echo "[stop-local] Done."
echo "[stop-local] If Spring Boot apps are still running, stop them in their terminals (Ctrl+C)."
