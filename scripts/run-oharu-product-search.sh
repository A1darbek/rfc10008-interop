#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMPLEMENTATION_DIR="${ROOT}/implementations/oharu-product-search"
IMPLEMENTATION_URL="https://github.com/oharu121/http-query-method-rfc10008-demo.git"
IMPLEMENTATION_COMMIT="057d9effae1bc767eaef03fc6cdc1b774cd735ad"
WORK_DIR="${ROOT}/.work/oharu-product-search"
PORT="${OHARU_PORT:-18082}"
ENDPOINT="http://127.0.0.1:${PORT}/products/search"
VENV="${WORK_DIR}/venv"
SERVER_PID=""

cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}"
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

mkdir -p "${ROOT}/implementations" "${WORK_DIR}"

if [[ ! -d "${IMPLEMENTATION_DIR}/.git" ]]; then
  git clone "${IMPLEMENTATION_URL}" "${IMPLEMENTATION_DIR}"
fi

git -C "${IMPLEMENTATION_DIR}" fetch --quiet origin
git -C "${IMPLEMENTATION_DIR}" checkout --quiet --detach "${IMPLEMENTATION_COMMIT}"
git -C "${IMPLEMENTATION_DIR}" restore --source="${IMPLEMENTATION_COMMIT}" --staged --worktree .

if curl --max-time 1 --silent --show-error "${ENDPOINT}" >/dev/null 2>&1; then
  echo "Port ${PORT} is already serving HTTP; set OHARU_PORT to an unused port." >&2
  exit 1
fi

if [[ ! -x "${VENV}/bin/python" ]]; then
  python3 -m venv "${VENV}"
fi

if ! "${VENV}/bin/python" -c 'import starlette, uvicorn' >/dev/null 2>&1; then
  "${VENV}/bin/python" -m pip install --disable-pip-version-check \
    "httpx==0.28.1" \
    "starlette==1.3.1" \
    "uvicorn==0.49.0"
fi

(
  cd "${IMPLEMENTATION_DIR}"
  exec "${VENV}/bin/python" -m uvicorn server:app \
    --host 127.0.0.1 \
    --port "${PORT}"
) >"${WORK_DIR}/server.log" 2>&1 &
SERVER_PID=$!

for _ in $(seq 1 80); do
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    sed -n '1,200p' "${WORK_DIR}/server.log" >&2
    exit 1
  fi
  if curl --max-time 1 --silent --fail \
    "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

if ! curl --max-time 1 --silent --fail \
  "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
  sed -n '1,200p' "${WORK_DIR}/server.log" >&2
  exit 1
fi

python3 "${ROOT}/adapters/oharu_product_search.py" \
  --endpoint "${ENDPOINT}" \
  --target "${ROOT}/targets/oharu-product-search/target.json" \
  --request-a "${ROOT}/targets/oharu-product-search/request-a.json" \
  --request-a-equivalent "${ROOT}/targets/oharu-product-search/request-a-equivalent.json" \
  --request-b "${ROOT}/targets/oharu-product-search/request-b.json" \
  --output "${ROOT}/receipts/oharu-product-search" \
  --sanitize

python3 "${ROOT}/runner/render_matrix.py"
