# Release Checklist

Do not publish until the native bridge has been compiled and smoke-tested on all
claimed target platforms.

## Before Tagging

- Confirm package name ownership and approval.
- Confirm bundled Betterleaks version in `bridge/go.mod`.
- Run `uv run python scripts/check_betterleaks_pin.py` to verify the
  Betterleaks version and exact module checksums.
- Run `uv run python scripts/bump_version.py --check`.
- Run `uv lock`.
- Run `uv run python scripts/build_native.py`.
- Run `uv run coverage run -m pytest`.
- Run `uv run coverage report`.
- Run `uv run ruff check .`.
- Run `uv run mypy python`.
- Run Go checks from `bridge/`: `gofmt`, `go test ./...`, `go vet ./...`,
  `staticcheck ./...`, and `govulncheck ./...`.
- Run `uv build --wheel` and confirm the wheel includes the native library and
  `py.typed`.
- Run `uv run python scripts/inspect_wheels.py <wheel-dir>`.
- Run `uv run python scripts/checksums.py <wheel-dir> --output ../release/SHA256SUMS`.
- Run `uv run python scripts/checksums.py <wheel-dir> --verify ../release/SHA256SUMS`.
- Do not publish sdists until source builds are explicitly supported.
- Run native smoke tests with the compiled library present.
- Run `uv run python benchmarks/bench.py --rounds 3 --warmups 1`.
- Run `bash e2e/run.sh` to verify a local wheel installs in a clean runtime
  image without a Go toolchain.
- Update README platform matrix if support changed.
- Update `docs/betterleaks-pin.md` if the Betterleaks version changed.
- Update release notes with the Python package version and bundled Betterleaks
  version.

## CI Release Flow

- Prepare release changes with either a normal local edit or the manual
  `Prepare Release` GitHub Actions workflow.
- Use a `release/vX.Y.Z` branch for release preparation when possible.
- CI, E2E, Wheels, Docs, and Benchmarks should pass before tagging.
- Merge the release branch to `main` after required checks and review pass.
- The `Tag Release` workflow creates tag `vX.Y.Z` when the merged PR branch was
  `release/vX.Y.Z` and `pyproject.toml` matches.
- The `Tag Release` workflow dispatches `Publish` after creating the tag. This
  explicit dispatch is required because tags pushed by `GITHUB_TOKEN` do not
  trigger normal tag-push workflows.
- Direct maintainer-created `v*` tag pushes still trigger the publish workflow.
- If a tag exists but publish did not run, start it manually with
  `gh workflow run publish.yml --ref main -f version=X.Y.Z`.
- GitHub Actions builds wheels on Linux, macOS, and Windows.
- Every wheel must install and run `scripts/wheel_smoke.py`.
- The Docker E2E workflow should build a local wheel, install it from `/tmp`,
  and run directory/text scans against fake fixture secrets.
- `publish.yml` downloads wheel artifacts, inspects them, writes
  `release/SHA256SUMS`, verifies those checksums, attests the release artifacts,
  uploads the checksum artifact, and publishes only wheel files from `dist`.
- The publish workflow creates or updates GitHub release notes and attaches
  `SHA256SUMS`.
- The publish workflow then runs `scripts/post_release_audit.py` to verify PyPI
  metadata, GitHub release assets, checksum parity, no musllinux artifacts, and
  a temporary-venv PyPI install smoke.
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
- Run `uv run python scripts/post_release_audit.py --version <version>`.
- Verify Docker install using `python:3.12-slim`.
- Download a wheel and confirm `pybetterleaks/py.typed` is included.
- Confirm no install-time downloads occur.
- Confirm `SHA256SUMS` is attached to the GitHub release.
- Confirm GitHub artifact attestations exist for wheels and checksums.
