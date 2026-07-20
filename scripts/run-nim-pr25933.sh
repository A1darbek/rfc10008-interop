#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NIM_DIR="$ROOT/.work/Nim"
NIM_SHA="a233362101230b5930c5fa0005980973d3ab3627"
AYDER_ENDPOINT="${AYDER_ENDPOINT:-http://127.0.0.1:1109/broker/query}"
AYDER_BODY='{"source":{"topic":"payment-recovery","partition":0,"from_offset":0,"to_offset":3,"limit":10,"sealed_only":true}}'

mkdir -p "$ROOT/.work"
if [[ ! -d "$NIM_DIR/.git" ]]; then
  git clone https://github.com/nim-lang/Nim.git "$NIM_DIR"
fi

git -C "$NIM_DIR" fetch --quiet origin +pull/25933/head:pr-25933
git -C "$NIM_DIR" checkout --quiet "$NIM_SHA"

export PATH="$NIM_DIR/bin:$PATH"
if ! command -v nim >/dev/null 2>&1 || ! nim --version | grep -q "$NIM_SHA"; then
  (
    cd "$NIM_DIR"
    sh build_all.sh
  )
fi

nim --version

mkdir -p "$ROOT/.work/nim-pr25933" "$ROOT/receipts/nim-pr25933-client" "$ROOT/receipts/nim-pr25933-server"

nim c -o:"$ROOT/.work/nim-pr25933/query_server" "$ROOT/fixtures/nim-pr25933/query_server.nim"
nim c -o:"$ROOT/.work/nim-pr25933/ayder_sync_client" "$ROOT/fixtures/nim-pr25933/ayder_sync_client.nim"
nim c -o:"$ROOT/.work/nim-pr25933/ayder_async_client" "$ROOT/fixtures/nim-pr25933/ayder_async_client.nim"
nim c -o:"$ROOT/.work/nim-pr25933/redirect_client" "$ROOT/fixtures/nim-pr25933/redirect_client.nim"

"$ROOT/.work/nim-pr25933/query_server" >"$ROOT/receipts/nim-pr25933-server/server.log" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18133/query -X QUERY -H 'Content-Type: application/json' -d '{}' >/dev/null; then
    break
  fi
  sleep 1
done

python3 "$ROOT/runner/run.py" \
  --target "$ROOT/targets/nim-pr25933/target.json" \
  --output "$ROOT/receipts/nim-pr25933-server"

"$ROOT/.work/nim-pr25933/ayder_sync_client" "$AYDER_ENDPOINT" "$AYDER_BODY" > "$ROOT/receipts/nim-pr25933-client/sync.json"
"$ROOT/.work/nim-pr25933/ayder_async_client" "$AYDER_ENDPOINT" "$AYDER_BODY" > "$ROOT/receipts/nim-pr25933-client/async.json"
"$ROOT/.work/nim-pr25933/redirect_client" http://127.0.0.1:18133 > "$ROOT/receipts/nim-pr25933-client/redirects.json"

python3 "$ROOT/adapters/nim_query.py" \
  --sync-client-json "$ROOT/receipts/nim-pr25933-client/sync.json" \
  --async-client-json "$ROOT/receipts/nim-pr25933-client/async.json" \
  --redirect-json "$ROOT/receipts/nim-pr25933-client/redirects.json" \
  --output "$ROOT/receipts/nim-pr25933-client"

python3 "$ROOT/runner/render_matrix.py"
