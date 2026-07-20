#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMPL="${LEDGER_IMPL:-$ROOT/implementations/ledger-query}"
OUT="$ROOT/receipts/ledger-query"
WORK="$ROOT/.work/ledger-query-generic"
GO_IMAGE="${GO_IMAGE:-golang@sha256:3aff6657219a4d9c14e27fb1d8976c49c29fddb70ba835014f477e1c70636647}"

"$ROOT/scripts/setup-ledger-query.sh"

mkdir -p "$OUT" "$WORK"

if ! command -v go >/dev/null 2>&1; then
  docker pull "$GO_IMAGE" >/dev/null
fi

(
  cd "$IMPL"
  if command -v go >/dev/null 2>&1; then
    DATABASE_URL="postgres://ledger:ledger@localhost:5434/ledger" \
    REDIS_ADDR="localhost:6379" \
    go run ./cmd/server >"$OUT/server.log" 2>&1 &
  else
    docker run --rm \
      -p 8080:8080 \
      --add-host host.docker.internal:host-gateway \
      -v "$IMPL:/src" \
      -w /src \
      -e DATABASE_URL="postgres://ledger:ledger@host.docker.internal:5434/ledger" \
      -e REDIS_ADDR="host.docker.internal:6379" \
      "$GO_IMAGE" go run ./cmd/server >"$OUT/server.log" 2>&1 &
  fi
  echo "$!" > "$ROOT/.work/ledger-query-server.pid"
)

SERVER_PID="$(cat "$ROOT/.work/ledger-query-server.pid")"
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

for _ in $(seq 1 180); do
  if curl -fsS http://localhost:8080/healthz >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    cat "$OUT/server.log" >&2
    exit 1
  fi
  sleep 1
done

curl -fsS http://localhost:8080/healthz >/dev/null

curl -fsS -X POST http://localhost:8080/charges \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: interop-charge-001' \
  -d '{
    "account_id":"11111111-1111-1111-1111-111111111111",
    "amount_cents":500,
    "currency":"USD"
  }' >/dev/null

curl -fsS -X POST http://localhost:8080/charges \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: interop-charge-002' \
  -d '{
    "account_id":"11111111-1111-1111-1111-111111111111",
    "amount_cents":1500,
    "currency":"USD"
  }' >/dev/null

python3 "$ROOT/runner/run.py" \
  --target "$ROOT/targets/ledger-query/target.json" \
  --output "$WORK"

python3 "$ROOT/adapters/ledger_query.py" \
  --implementation-dir "$IMPL" \
  --generic-receipt "$WORK/receipt.json" \
  --output "$OUT" \
  --go-image "$GO_IMAGE"

python3 "$ROOT/runner/render_matrix.py"
