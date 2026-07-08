# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=python:3.13-slim
ARG GO_VERSION=1.26.3

FROM ${PYTHON_IMAGE} AS builder

ARG GO_VERSION
ARG TARGETARCH

WORKDIR /src

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
RUN case "${TARGETARCH}" in \
      amd64) GO_ARCH="amd64" ;; \
      arm64) GO_ARCH="arm64" ;; \
      *) echo "Unsupported target architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
    && curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-${GO_ARCH}.tar.gz" -o /tmp/go.tgz \
    && tar -C /usr/local -xzf /tmp/go.tgz \
    && rm /tmp/go.tgz \
    && /usr/local/go/bin/go version
ENV PATH="/usr/local/go/bin:${PATH}"
RUN python -m pip install --upgrade pip \
    && python -m pip install "build>=1.2.2" "setuptools>=70.1" wheel

COPY pyproject.toml setup.py README.md LICENSE ./
COPY bridge ./bridge
COPY python ./python
COPY scripts ./scripts

RUN rm -f python/pybetterleaks/native/*.dll \
    python/pybetterleaks/native/*.dylib \
    python/pybetterleaks/native/*.h \
    python/pybetterleaks/native/*.so
RUN python scripts/build_native.py
RUN python -m build --wheel --no-isolation --outdir /tmp/pybetterleaks-wheelhouse

FROM ${PYTHON_IMAGE} AS runtime

WORKDIR /e2e

ENV PYBETTERLEAKS_E2E_EXPECT_NO_GO=1

COPY --from=builder /tmp/pybetterleaks-wheelhouse /tmp/pybetterleaks-wheelhouse
RUN python -m pip install --no-index --find-links=/tmp/pybetterleaks-wheelhouse pybetterleaks

COPY e2e/fixtures ./fixtures
COPY e2e/runner.py ./runner.py

CMD ["python", "runner.py"]
