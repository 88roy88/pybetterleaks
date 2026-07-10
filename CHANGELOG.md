# Changelog

All notable PyBetterleaks release notes live here. PyBetterleaks uses its own
Python package version and documents the bundled Betterleaks engine version
separately.

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
