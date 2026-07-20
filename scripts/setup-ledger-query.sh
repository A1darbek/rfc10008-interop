#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMPL="${LEDGER_IMPL:-$ROOT/implementations/ledger-query}"
SHA="e60d86d978b212e2b7794b7d6cdb8bf0b03b49c2"

mkdir -p "$ROOT/implementations"
if [[ ! -d "$IMPL/.git" ]]; then
  git clone https://github.com/Keshav-behl/LEDGER-QUERY.git "$IMPL"
fi

git -C "$IMPL" fetch --quiet origin
git -C "$IMPL" checkout --quiet "$SHA"

docker compose -f "$IMPL/docker-compose.yml" down -v
docker compose -f "$IMPL/docker-compose.yml" up -d

for _ in $(seq 1 90); do
  if docker compose -f "$IMPL/docker-compose.yml" exec -T postgres psql -U ledger -d ledger -tA -c 'SELECT 1' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker compose -f "$IMPL/docker-compose.yml" exec -T postgres psql -U ledger -d ledger -tA -c 'SELECT 1' >/dev/null

docker compose -f "$IMPL/docker-compose.yml" exec -T postgres psql -U ledger -d ledger -v ON_ERROR_STOP=1 < "$IMPL/migrations/0001_init.up.sql"

docker compose -f "$IMPL/docker-compose.yml" exec -T postgres psql -U ledger -d ledger -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO accounts (
  id,
  name,
  balance_cents,
  currency
)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  'rfc10008-interop',
  0,
  'USD'
)
ON CONFLICT (id) DO NOTHING;
SQL

docker compose -f "$IMPL/docker-compose.yml" exec -T redis redis-cli FLUSHDB >/dev/null
