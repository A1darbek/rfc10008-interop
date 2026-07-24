#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMPL_DIR="${LARAVEL13_IMPL:-$ROOT/implementations/laravel-http-query-demo}"
SHA="6dad5145eececc7c137b89c9cd4cce56fa83a8b5"
HOST_PORT="${LARAVEL13_PORT:-18081}"
ENDPOINT="http://localhost:${HOST_PORT}/mock/orders"
OUT="$ROOT/receipts/laravel13-query-comparison"
WORK_DIR="$ROOT/.work/laravel13-query-comparison"
WORK_CONTEXT="$WORK_DIR/context"
WORK_DOCKERFILE="$WORK_DIR/Dockerfile.php83"

mkdir -p "$ROOT/implementations"
if [[ ! -d "$IMPL_DIR/.git" ]]; then
  git clone https://github.com/phoenix1331/laravel-http-query-demo.git "$IMPL_DIR"
fi

git -C "$IMPL_DIR" fetch --quiet origin
git -C "$IMPL_DIR" checkout --quiet "$SHA"
git -C "$IMPL_DIR" restore --source="$SHA" --worktree --staged Dockerfile

SOURCE_DOCKERFILE="$IMPL_DIR/Dockerfile"
grep -q '^FROM php:8.2-apache$' "$SOURCE_DOCKERFILE" || {
  echo "unexpected pinned Dockerfile base image" >&2
  exit 1
}

rm -rf "$WORK_CONTEXT"
mkdir -p "$WORK_CONTEXT" "$WORK_DIR"
(
  cd "$IMPL_DIR"
  tar --exclude=.git -cf - .
) | (
  cd "$WORK_CONTEXT"
  tar -xf -
)

sed \
  's/^FROM php:8.2-apache$/FROM php:8.3-apache/' \
  "$SOURCE_DOCKERFILE" \
  > "$WORK_DOCKERFILE"
cp "$WORK_DOCKERFILE" "$WORK_CONTEXT/Dockerfile"
sed \
  -e "s/\"8080:80\"/\"${HOST_PORT}:80\"/" \
  -e "s#http://localhost:8080#http://localhost:${HOST_PORT}#g" \
  "$WORK_CONTEXT/docker-compose.yml" \
  > "$WORK_CONTEXT/docker-compose.yml.tmp"
mv "$WORK_CONTEXT/docker-compose.yml.tmp" "$WORK_CONTEXT/docker-compose.yml"

docker compose -f "$IMPL_DIR/docker-compose.yml" down -v
docker compose -f "$WORK_CONTEXT/docker-compose.yml" down -v
docker compose -f "$WORK_CONTEXT/docker-compose.yml" up -d --build

for _ in $(seq 1 90); do
  if curl -fsS "http://localhost:${HOST_PORT}/demo" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

curl -fsS "http://localhost:${HOST_PORT}/demo" >/dev/null

mkdir -p "$OUT" "$WORK_DIR/generic"

python3 "$ROOT/runner/run.py" \
  --target "$ROOT/targets/laravel13-query-comparison/target.json" \
  --output "$WORK_DIR/generic"

python3 "$ROOT/adapters/laravel13_native.py" \
  --implementation-dir "$WORK_CONTEXT" \
  --generic-receipt "$WORK_DIR/generic/receipt.json" \
  --endpoint "$ENDPOINT" \
  --output "$OUT"

python3 "$ROOT/runner/render_matrix.py"
