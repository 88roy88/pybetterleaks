# Release Checklist

Do not publish until the native bridge has been compiled and smoke-tested on all
claimed target platforms.

## Before Tagging

- Confirm package name ownership and approval.
- Confirm bundled Betterleaks version in `bridge/go.mod`.
- Run `uv run python scripts/check_betterleaks_pin.py`.
- Run `uv lock`.
- Run `uv run python scripts/build_native.py`.
- Run `uv run pytest`.
- Run `uv run ruff check .`.
- Run `uv run mypy python`.
- Run Go checks from `bridge/`: `gofmt`, `go test ./...`, `go vet ./...`,
  `staticcheck ./...`, and `govulncheck ./...`.
- Run `uv build --wheel` and confirm the wheel includes the native library and
  `py.typed`.
- Run `uv build --sdist` and confirm the sdist does not include generated native
  libraries.
- Run native smoke tests with the compiled library present.
- Run `uv run python benchmarks/bench.py --rounds 3 --warmups 1`.
- Run `bash e2e/run.sh` to verify a local wheel installs in a clean runtime
  image without a Go toolchain.
- Update README platform matrix if support changed.
- Update `docs/betterleaks-pin.md` if the Betterleaks version changed.
- Update release notes with the Python package version and bundled Betterleaks
  version.

## CI Release Flow

- Push a tag like `v0.3.0`.
- GitHub Actions builds wheels on Linux, macOS, and Windows.
- Every wheel must install and run `scripts/wheel_smoke.py`.
- The Docker E2E workflow should build a local wheel, install it from `/tmp`,
  and run directory/text scans against fake fixture secrets.
- `publish.yml` downloads wheel artifacts, writes `release/SHA256SUMS`, uploads
  the checksum artifact, and publishes only wheel files from `dist`.
- The publish workflow then runs `scripts/pypi_smoke.py` to install the
  published version from PyPI in a temporary virtual environment.
- Publish wheels to PyPI through trusted publishing only.
- Do not publish sdists until source builds are explicitly supported.

## Musllinux Gate

Musllinux/Alpine is explicitly unsupported and must not be published as a wheel
target without a clean loader proof that avoids `LD_PRELOAD`, wrapper launchers,
or user-side runtime changes.

Current blocker:

```text
initial-exec TLS resolves to dynamic definition
```

Do not add musllinux wheels to the publish matrix while that loader failure is
reproducible.

## After Publishing

- Verify `pip install pybetterleaks` in a clean environment.
- Verify `pip install --only-binary=:all: pybetterleaks`.
- Run `uv run python scripts/pypi_smoke.py --version <version>`.
- Verify Docker install using `python:3.12-slim`.
- Download a wheel and confirm `pybetterleaks/py.typed` is included.
- Confirm no install-time downloads occur.
- Publish checksum values with the GitHub release notes.
