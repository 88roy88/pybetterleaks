#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${PYBETTERLEAKS_E2E_IMAGE:-pybetterleaks-e2e:local}"
PYTHON_IMAGE="${PYBETTERLEAKS_E2E_PYTHON_IMAGE:-python:3.13-slim}"

docker build \
  --build-arg "PYTHON_IMAGE=${PYTHON_IMAGE}" \
  -f "${ROOT}/e2e/Dockerfile" \
  -t "${IMAGE}" \
  "${ROOT}"

docker run --rm "${IMAGE}"
