#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMPL_DIR="${LARAVEL13_IMPL:-$ROOT/implementations/laravel-http-query-demo}"
SHA="af19ed98eb77b62f5156ce285dc2ea135788519a"
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

docker compose -f "$IMPL_DIR/docker-compose.yml" down -v
docker compose -f "$WORK_CONTEXT/docker-compose.yml" down -v
docker compose -f "$WORK_CONTEXT/docker-compose.yml" up -d --build

for _ in $(seq 1 90); do
  if curl -fsS http://localhost:8080/demo >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

curl -fsS http://localhost:8080/demo >/dev/null

mkdir -p "$OUT" "$WORK_DIR/generic"

python3 "$ROOT/runner/run.py" \
  --target "$ROOT/targets/laravel13-query-comparison/target.json" \
  --output "$WORK_DIR/generic"

python3 "$ROOT/adapters/laravel13_native.py" \
  --implementation-dir "$WORK_CONTEXT" \
  --generic-receipt "$WORK_DIR/generic/receipt.json" \
  --output "$OUT"

python3 "$ROOT/runner/render_matrix.py"
