# Changelog

All notable PyBetterleaks release notes live here. PyBetterleaks uses its own
Python package version and documents the bundled Betterleaks engine version
separately.

## 0.6.1 - 2026-07-13

Release theme: Betterleaks pin verification and release-flow hardening.

Bundled Betterleaks: `v1.6.1`

### Added

- Added exact checksum verification for the pinned Betterleaks Go module and
  its `go.mod` entry.
- Added unit coverage for Betterleaks pin drift, missing checksum lines,
  checksum mismatches, and unrecorded Betterleaks upgrades.

### Changed

- The publish workflow can now be dispatched manually with an explicit version.
- The release-tag workflow now dispatches publishing after creating a tag,
  avoiding GitHub's ignored workflow-created tag-push events.
- Hardened post-release audit retries so PyPI metadata and checksum validation
  are retried together while PyPI propagates new files.
- Documented the exact Betterleaks checksum pin in the supply-chain docs.

## 0.6.0 - 2026-07-13

Release theme: release automation, benchmark artifacts, and project polish.

Bundled Betterleaks: `v1.6.1`

### Added

- Added version bump/check tooling and CI version synchronization checks.
- Added a manual release-preparation workflow for `release/vX.Y.Z` branches.
- Added merge-to-main release tagging for reviewed `release/vX.Y.Z` branches.
- Added post-release audit automation for PyPI metadata, GitHub release assets,
  checksums, no-musllinux enforcement, and temporary-venv install smoke checks.
- Added benchmark JSON/Markdown artifact output plus a CI benchmark workflow.
- Added a clean-wheel benchmark smoke runner.
- Added GitHub issue templates, PR template, and `SECURITY.md`.
- Added `CODEOWNERS` for maintainer review enforcement.
- Added a dedicated public Git scanning guide.
- Added README visual polish with a hero asset.

### Changed

- Refreshed GitHub Actions major versions to reduce Node runtime deprecation
  noise.
- Release branches now run heavier CI gates before tags are cut.
- The publish workflow now performs the full post-release audit after GitHub
  release notes and `SHA256SUMS` are available.

## 0.5.0 - 2026-07-13

Release theme: publish-path hardening.

Bundled Betterleaks: `v1.6.1`

### Added

- Added wheel artifact inspection before publishing.
- Added wheel checks that reject accidental universal wheels and unsupported
  musllinux wheels.
- Added wheel checks that verify each artifact includes `py.typed` and exactly
  one packaged native library for the target platform.
- Added checksum generation and verification for release artifacts.
- Added GitHub generated release notes with `SHA256SUMS` upload.
- Added GitHub artifact attestations for wheels and checksums.
- Added grouped GitHub release-note configuration through `.github/release.yml`.
- Added release-tool unit tests with synthetic wheel artifacts and checksum
  fixtures.
- Added supply-chain and deprecation-policy documentation.

### Changed

- Built the native bridge before Python coverage in CI so native smoke tests are
  included in the coverage gate.
- Ran wheel artifact inspection after `cibuildwheel` and again in the publish
  workflow before PyPI upload.
- Hardened the publish workflow around artifact checks before PyPI upload.
- Verified generated `SHA256SUMS` before publishing or attaching release assets.
- Kept PyPI publishing tokenless through trusted publishing.

### Notes

- v0.5 deliberately kept sdists, musllinux/Alpine wheels, and SBOM generation
  out of scope.

## 0.4.0 - 2026-07-10

Release theme: config ergonomics and async cancellation polish.

Bundled Betterleaks: `v1.6.1`

### Added

- Added modern `Expr` helpers for entropy, token efficiency, finding filters,
  attribute filters, path filters, Git commit filters, and boolean composition.
- Added `Validation` helpers for common validation-result expressions.
- Added common `Rule` constructors for regex, path, prefixed token, and PEM
  private-key rules.
- Added `Rule.entropy` compatibility serialization for Betterleaks TOML.
- Added `extend_base_path` handling for relative inline `[extend].path` values.
- Added stronger release metadata and roadmap/backlog cleanup.

### Changed

- Hardened async cancellation cleanup by shielding and draining executor
  futures after requesting native cancellation.
- Marked Betterleaks `v1.6.1` stable config-helper coverage as complete.

### Notes

- Musllinux/Alpine wheels remain unsupported because Python `ctypes` loading of
  Go shared libraries on musl still fails with the known TLS loader issue.
- A post-release CI fix builds the native bridge before Python coverage so
  native smoke tests run in GitHub Actions instead of being skipped.

## 0.3.1 - 2026-07-09

Release theme: PyPI publication confidence and v1 readiness documentation.

Bundled Betterleaks: `v1.6.1`

### Added

- Added post-publish PyPI smoke testing from a temporary virtual environment.
- Added v1 readiness criteria and release-readiness documentation.
- Added clearer release docs around package ownership, trusted publishing, and
  supported artifacts.

### Changed

- Polished README/PyPI-facing project metadata after the first public package
  publication path was established.

## 0.3.0 - 2026-07-09

Release theme: local Git worktree scanning.

Bundled Betterleaks: `v1.6.1`

### Added

- Added `scan_git(..., scope="worktree")`.
- Added `scan_git_async(...)`.
- Added `GitScope = Literal["worktree"]` and `SUPPORTED_GIT_SCOPES`.
- Added local repository fixtures and tests for worktree scanning.
- Added structured errors for unsupported Git scopes and invalid repositories.
- Added project backlog coverage for deferred Git scopes, streaming, providers,
  platforms, and release trust.

### Notes

- Git history, diff, staged-only, and tracked-only scopes remain deferred until
  they can preserve the no-runtime-subprocess promise.

## 0.2.0 - 2026-07-09

Release theme: typed configuration, async wrappers, cancellation, and
benchmarks.

Bundled Betterleaks: `v1.6.1`

### Added

- Added typed config models: `BetterleaksConfig`, `Rule`, `Extend`, `Expr`, and
  `RequiredRule`.
- Added inline TOML config handoff through the native JSON ABI.
- Added `scan_text_async` and `scan_dir_async`.
- Added cooperative native cancellation by request id.
- Added validation env var bridging for Betterleaks validators.
- Added synthetic benchmarks with optional Betterleaks CLI comparison.
- Added release checksum tooling.
- Added Docker E2E coverage on a glibc Python runtime image.

### Notes

- Musllinux/Alpine support was investigated and deferred because the Go shared
  library failed to load under musl.

## 0.1.0 - 2026-07-09

Release theme: first Python-native Betterleaks SDK candidate.

Bundled Betterleaks: `v1.6.1`

### Added

- Added the `pybetterleaks` Python package scaffold.
- Added the Go `c-shared` bridge with a JSON ABI.
- Added `ctypes` native loading from `pybetterleaks/native/`.
- Added `scan_text`, `scan_dir`, and `betterleaks_version`.
- Added typed dataclass results for findings, errors, and scan results.
- Added `py.typed` packaging.
- Added platform wheel packaging with bundled native libraries.
- Added Python tests, native smoke tests, wheel smoke tests, and initial CI.

### Notes

- Runtime subprocesses and runtime Betterleaks CLI calls are intentionally not
  part of the supported SDK design.
