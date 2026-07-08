# Release Checklist

Do not publish until the native bridge has been compiled and smoke-tested on all
target platforms.

## Before Tagging

- Confirm package name ownership and approval.
- Confirm bundled Betterleaks version in `bridge/go.mod`.
- Run `uv run python scripts/check_betterleaks_pin.py`.
- Run `uv lock`.
- Run `uv run pytest`.
- Run `uv run ruff check .`.
- Run `uv run mypy python`.
- Run Go checks from `bridge/`: `gofmt`, `go test ./...`, `go vet ./...`,
  `staticcheck ./...`, and `govulncheck ./...`.
- Run `uv run python scripts/build_native.py` on a machine with Go installed.
- Run `uv build --wheel` and confirm the wheel includes the native library and
  `py.typed`.
- Run `uv build --sdist` and confirm the sdist does not include generated native
  libraries.
- Run native smoke tests with the compiled library present.
- Run `bash e2e/run.sh` to verify a local wheel installs in a clean runtime
  image without a Go toolchain.
- Run `bash e2e/run-alpine.sh` before claiming musllinux/Alpine support. It is
  currently a known failing canary for the musl Go `c-shared` loader blocker.
- Update README platform matrix if support changed.
- Update `docs/betterleaks-pin.md` if the Betterleaks version changed.
- Update release notes with the bundled Betterleaks version.

## CI Release Flow

- Push a tag like `v0.1.0`.
- GitHub Actions builds wheels on Linux, macOS, and Windows.
- Every wheel must install and run `betterleaks_version()`.
- Native scan smoke tests should run against a fake fixture.
- The Docker E2E workflow should build a local wheel, install it from `/tmp`,
  and run directory/text scans against fake fixture secrets.
- Publish wheels to PyPI through trusted publishing only. Do not publish sdists
  for v0.1 unless source builds are explicitly supported.

## After Publishing

- Verify `pip install pybetterleaks` in a clean environment.
- Verify `pip install --only-binary=:all: pybetterleaks`.
- Verify Docker install using `python:3.12-slim`.
- Download a wheel and confirm `pybetterleaks/py.typed` is included.
- Confirm no install-time downloads occur.
