#!/usr/bin/env bash
set -euo pipefail
AYDER_DIR="${1:-../ayder}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cd "$AYDER_DIR"
AYDER_COMMIT="$(git rev-parse HEAD)"
DOCKER_VERSION="$(docker --version 2>/dev/null || true)"
docker compose up -d --build
./demos/http_query_recovery_snapshot/run_demo.sh
LATEST_DIR="$(find artifacts/http_query_recovery_snapshot -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)"
cd "$ROOT"
mkdir -p receipts/ayder/safety
cp "$AYDER_DIR/$LATEST_DIR/receipt.json" receipts/ayder/safety/receipt.json
cp "$AYDER_DIR/$LATEST_DIR/receipt.txt" receipts/ayder/safety/receipt.txt
cat > receipts/ayder/safety/metadata.json <<JSON
{
  "schema_version": "0.1",
  "generated_at": "$STAMP",
  "ayder_commit": "$AYDER_COMMIT",
  "interop_runner_commit": "$(git rev-parse HEAD)",
  "docker_version": "$DOCKER_VERSION",
  "demo_script_path": "demos/http_query_recovery_snapshot/run_demo.sh"
}
JSON
