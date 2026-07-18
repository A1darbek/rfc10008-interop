#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMPL="$ROOT/implementations/laravel-http-query-demo"
SHA="c9a2c8b325bad46f87aa7e065046afa1de5aafd5"

if [[ ! -d "$IMPL/.git" ]]; then
  mkdir -p "$(dirname "$IMPL")"
  git clone https://github.com/phoenix1331/laravel-http-query-demo.git "$IMPL"
fi

git -C "$IMPL" fetch --quiet origin
git -C "$IMPL" checkout --quiet "$SHA"

docker compose -f "$IMPL/docker-compose.yml" down -v
docker compose -f "$IMPL/docker-compose.yml" up -d --build

for _ in $(seq 1 60); do
  if curl -fsS http://localhost:8080/demo >/dev/null; then
    break
  fi
  sleep 1
done

curl -fsS http://localhost:8080/demo >/dev/null

python3 "$ROOT/runner/run.py" \
  --target "$ROOT/targets/laravel12-apache/target.json" \
  --output "$ROOT/receipts/laravel12-apache"

python3 "$ROOT/adapters/laravel12_apache.py" \
  --endpoint http://localhost:8080/mock/orders \
  --compose-file "$IMPL/docker-compose.yml" \
  --output "$ROOT/receipts/laravel12-apache"

python3 "$ROOT/runner/render_matrix.py"
