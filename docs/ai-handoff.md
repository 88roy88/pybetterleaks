# AI Handoff

This file is for future AI agents and human maintainers. It compresses the
research and decisions made so far.

## User Intent

The user wants a Python integration for Betterleaks. They explicitly do not want
a package that merely shells out with `subprocess` or `popen`. They want a
self-contained PyPI package that is easy to use in Docker and can be built by CI
for multiple platforms.

## Current Repository State

As of 2026-07-08:

- Workspace: `/Users/roymezan/Documents/BetterLeaksPython`
- Git branch: `main`
- Repo status at docs creation: no commits yet
- Python SDK, Go bridge, tests, Docker E2E, CI workflows, and docs are present
- Go was installed with Homebrew after the initial scaffold
- Local Go observed after installation: `go1.26.5 darwin/arm64`
- Local macOS arm64 native library build succeeded
- `scan_dir` uses Betterleaks `sources.Files` plus `Detector.Run`, preserving
  path metadata, prefilters, archive handling, and context cancellation.
- `scan_text` also uses `Detector.Run` through a small in-memory source so
  validation and timeout behavior share the same path.
- `MANIFEST.in` excludes generated native libraries from sdists; v0.1 release
  should publish CI-built wheels only.

## Recommended Technical Path

Build a Python package that bundles a Go shared library bridge:

```text
Python package
  -> ctypes or cffi
    -> Go shared library built with -buildmode=c-shared
      -> Betterleaks Go packages
```

Use JSON across the C ABI. Keep the ABI tiny:

- `BetterleaksScanJSON`
- `BetterleaksFree`
- `BetterleaksVersion`

Do not use runtime subprocesses to call the Betterleaks CLI.

## Betterleaks Facts To Reconfirm Before Coding

The following were checked on 2026-07-08 and may change:

- Betterleaks repo: <https://github.com/betterleaks/betterleaks>
- Latest release observed: `v1.6.1`, dated 2026-06-30
- Main language: Go
- License observed: MIT
- Important packages: `detect`, `config`, `sources`, `report`
- `detect.Detector.Run(ctx, source)` exists on the checked main branch
- `detect.Detector.DetectString(content string)` exists on the checked main
  branch
- `sources.Source` is an interface with a `Fragments` method

Before implementing, fetch or vendor the exact Betterleaks version to pin and
inspect the current APIs locally. Avoid coding from memory alone.

## First Implementation Steps

1. Run CI on Linux/macOS/Windows to validate wheel builds outside this machine.
2. Expand native fixtures beyond the current smoke checks.
3. Decide whether to publish a pre-release to TestPyPI.
4. Coordinate package naming with Betterleaks maintainers before a public PyPI release.

## Important Constraints

- Use `apply_patch` for manual file edits in this environment.
- Do not revert user changes.
- Do not publish to PyPI without explicit user approval.
- Do not run destructive Git commands.
- Network is restricted in this environment. If dependency fetching is required
  and sandboxed commands fail due to network, request escalation.

## Design Decisions Already Made

- Runtime subprocess wrapper: rejected.
- Native Go bridge: accepted recommended path.
- JSON ABI: recommended for stability and simplicity.
- Self-contained wheels: required.
- Install-time binary downloads: rejected.
- Manylinux first, musllinux later: recommended.
- API should start with `scan_text` and `scan_dir`.

## Open Questions

- Final PyPI package name.
- Whether to coordinate with Betterleaks maintainers before publishing.
- Whether to add source-build support later. v0.1 should publish wheels only.
- Whether CI should add Linux arm64 before the first PyPI release.
- Whether validation should stay default-off after broader testing.

## Useful Commands Once Code Exists

```bash
uv sync --all-extras --dev
uv run python scripts/build_native.py
uv run pytest
uv run ruff check .
uv run mypy python
uv build --wheel
bash e2e/run.sh
```

Use `uv build --sdist` only to inspect the source archive. It should not contain
generated native libraries, and v0.1 should not publish sdists.

## References

- Shared planning chat:
  <https://chatgpt.com/share/6a4e9907-1608-83eb-81e0-c92a48eb8a7a>
- Betterleaks repository:
  <https://github.com/betterleaks/betterleaks>
- Betterleaks detector source:
  <https://raw.githubusercontent.com/betterleaks/betterleaks/main/detect/detect.go>
- Go build modes:
  <https://pkg.go.dev/cmd/go#hdr-Build_modes>
- cibuildwheel:
  <https://cibuildwheel.pypa.io/en/stable/>
