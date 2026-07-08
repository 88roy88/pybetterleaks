#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${PYBETTERLEAKS_E2E_ALPINE_IMAGE:-pybetterleaks-e2e:alpine}"
PYTHON_IMAGE="${PYBETTERLEAKS_E2E_ALPINE_PYTHON_IMAGE:-python:3.13-alpine}"

docker build \
  --build-arg "PYTHON_IMAGE=${PYTHON_IMAGE}" \
  -f "${ROOT}/e2e/Dockerfile.alpine" \
  -t "${IMAGE}" \
  "${ROOT}"

docker run --rm "${IMAGE}"
