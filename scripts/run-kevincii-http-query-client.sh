#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMPLEMENTATION_DIR="${ROOT}/implementations/kevincii-http-query-client"
IMPLEMENTATION_URL="https://github.com/Kevinci/http-query.git"
IMPLEMENTATION_COMMIT="7fb3f7c4ff8b66a5bfd6678006e198ba3d18e647"
EXAMPLE_DIR="${IMPLEMENTATION_DIR}/examples/rfc10008-interop"
FIXTURE_DIR="${ROOT}/fixtures/kevincii-http-query-client"
AYDER_DIR="${ROOT}/implementations/ayder-kevincii"
AYDER_URL="https://github.com/A1darbek/ayder.git"
AYDER_COMMIT="2ddb6e346194c445445b04a4ffa5d1f9f700eaf2"
AYDER_IMAGE="rfc10008-kevincii-ayder:2ddb6e3"
AYDER_CONTAINER="rfc10008-kevincii-ayder"
AYDER_PORT="${KEVINCII_AYDER_PORT:-18109}"
ENDPOINT="http://127.0.0.1:${AYDER_PORT}/broker/query"
CONTAINER_STARTED="false"

cleanup() {
  if [[ "${CONTAINER_STARTED}" == "true" ]]; then
    docker stop "${AYDER_CONTAINER}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

mkdir -p "${ROOT}/implementations" "${ROOT}/.work/kevincii-http-query-client"

if [[ ! -d "${IMPLEMENTATION_DIR}/.git" ]]; then
  git clone "${IMPLEMENTATION_URL}" "${IMPLEMENTATION_DIR}"
fi
git -C "${IMPLEMENTATION_DIR}" fetch --quiet origin
git -C "${IMPLEMENTATION_DIR}" checkout --quiet --detach "${IMPLEMENTATION_COMMIT}"
git -C "${IMPLEMENTATION_DIR}" restore --source="${IMPLEMENTATION_COMMIT}" --staged --worktree .

if [[ ! -d "${AYDER_DIR}/.git" ]]; then
  git clone "${AYDER_URL}" "${AYDER_DIR}"
fi
git -C "${AYDER_DIR}" fetch --quiet origin
git -C "${AYDER_DIR}" checkout --quiet --detach "${AYDER_COMMIT}"
git -C "${AYDER_DIR}" restore --source="${AYDER_COMMIT}" --staged --worktree .

node -e 'const major=Number(process.versions.node.split(".")[0]); if (major < 20) process.exit(1)'

cp "${FIXTURE_DIR}/ayder-client.ts" "${EXAMPLE_DIR}/src/interop-ayder-client.ts"
cp "${FIXTURE_DIR}/fallback-harness.ts" "${EXAMPLE_DIR}/src/interop-fallback-harness.ts"
cp "${FIXTURE_DIR}/timeout-harness.ts" "${EXAMPLE_DIR}/src/interop-timeout-harness.ts"

(
  cd "${EXAMPLE_DIR}"
  npm ci
  npm run typecheck
)

if docker container inspect "${AYDER_CONTAINER}" >/dev/null 2>&1; then
  echo "Container ${AYDER_CONTAINER} already exists; refusing to replace it." >&2
  exit 1
fi

docker build --tag "${AYDER_IMAGE}" "${AYDER_DIR}"
docker run --rm --detach \
  --name "${AYDER_CONTAINER}" \
  --shm-size 2g \
  --security-opt seccomp=unconfined \
  --publish "127.0.0.1:${AYDER_PORT}:1109" \
  "${AYDER_IMAGE}" >/dev/null
CONTAINER_STARTED="true"

for _ in $(seq 1 120); do
  if ! docker container inspect "${AYDER_CONTAINER}" >/dev/null 2>&1; then
    echo "Ayder container exited before becoming healthy." >&2
    exit 1
  fi
  if curl --max-time 1 --silent --fail \
    "http://127.0.0.1:${AYDER_PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! curl --max-time 1 --silent --fail \
  "http://127.0.0.1:${AYDER_PORT}/health" >/dev/null 2>&1; then
  docker logs "${AYDER_CONTAINER}" >&2
  exit 1
fi

python3 "${ROOT}/adapters/kevincii_http_query_client.py" \
  --target "${ROOT}/targets/kevincii-http-query-client/target.json" \
  --implementation-dir "${IMPLEMENTATION_DIR}" \
  --example-dir "${EXAMPLE_DIR}" \
  --endpoint "${ENDPOINT}" \
  --output "${ROOT}/receipts/kevincii-http-query-client" \
  --sanitize

python3 "${ROOT}/runner/render_matrix.py"
