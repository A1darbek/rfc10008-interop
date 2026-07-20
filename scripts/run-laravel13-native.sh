#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMPL="${LARAVEL13_IMPL:-$ROOT/implementations/laravel-http-query-demo}"
SHA="af19ed98eb77b62f5156ce285dc2ea135788519a"
OUT="$ROOT/receipts/laravel13-native"
WORK="$ROOT/.work/laravel13-native-generic"

mkdir -p "$ROOT/implementations"
if [[ ! -d "$IMPL/.git" ]]; then
  git clone https://github.com/phoenix1331/laravel-http-query-demo.git "$IMPL"
fi

git -C "$IMPL" fetch --quiet origin
git -C "$IMPL" checkout --quiet "$SHA"

# The pinned Laravel 13 lockfile requires PHP ^8.3, while the demo branch's
# Dockerfile still names php:8.2-apache. Patch the local ignored checkout so
# the target can run without changing Darren's repository.
perl -0pi -e 's/php:8\.2-apache/php:8.3-apache/g' "$IMPL/Dockerfile"

docker compose -f "$IMPL/docker-compose.yml" down -v
docker compose -f "$IMPL/docker-compose.yml" up -d --build

for _ in $(seq 1 90); do
  if curl -fsS http://localhost:8080/demo >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

curl -fsS http://localhost:8080/demo >/dev/null

mkdir -p "$OUT" "$WORK"

python3 "$ROOT/runner/run.py" \
  --target "$ROOT/targets/laravel13-native/target.json" \
  --output "$WORK"

python3 "$ROOT/adapters/laravel13_native.py" \
  --implementation-dir "$IMPL" \
  --generic-receipt "$WORK/receipt.json" \
  --output "$OUT"

python3 "$ROOT/runner/render_matrix.py"
