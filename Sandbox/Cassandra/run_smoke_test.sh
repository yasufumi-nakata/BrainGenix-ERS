#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="${CASSANDRA_SERVICE_NAME:-cassandra}"
READY_RETRIES="${CASSANDRA_READY_RETRIES:-60}"
READY_SLEEP_SECONDS="${CASSANDRA_READY_SLEEP_SECONDS:-5}"
CLEANUP="${CASSANDRA_SMOKE_CLEANUP:-0}"

if [[ "${1:-}" == "--cleanup" ]]; then
  CLEANUP=1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to run the Cassandra smoke test." >&2
  exit 127
fi

cd "${SCRIPT_DIR}"

cleanup() {
  if [[ "${CLEANUP}" == "1" ]]; then
    docker compose down -v
  fi
}
trap cleanup EXIT

echo "Starting Cassandra sandbox..."
docker compose up -d "${SERVICE_NAME}"

echo "Waiting for Cassandra CQL readiness..."
for ((attempt = 1; attempt <= READY_RETRIES; attempt++)); do
  if docker compose exec -T "${SERVICE_NAME}" cqlsh -e "DESCRIBE KEYSPACES" >/dev/null 2>&1; then
    echo "Cassandra is ready."
    break
  fi

  if (( attempt == READY_RETRIES )); then
    echo "Cassandra did not become ready after ${READY_RETRIES} attempts." >&2
    docker compose logs --tail=120 "${SERVICE_NAME}" >&2 || true
    exit 1
  fi

  sleep "${READY_SLEEP_SECONDS}"
done

echo "Loading ERS Cassandra sandbox schema..."
docker compose exec -T "${SERVICE_NAME}" cqlsh -f /workspace/schema/00_braingenix_ers_sandbox.cql

echo "Running ERS Cassandra smoke queries..."
docker compose exec -T "${SERVICE_NAME}" cqlsh -f /workspace/queries/01_smoke_test.cql

echo "Cassandra smoke test completed successfully."
