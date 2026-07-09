# Workplan

## Goal

Ship a self-contained Python package that wraps Betterleaks through a bundled
Go shared library and publishes installable platform wheels to PyPI.

The end-state should feel like this:

```bash
pip install pybetterleaks
```

```python
from pybetterleaks import scan_dir

result = scan_dir(".")
```

No runtime subprocess, no Go toolchain for users, no Betterleaks CLI dependency,
and no binary downloads during installation.

## Phase 0: Project Setup

Deliverables:

- Choose package name.
- Create repository layout.
- Add initial Python packaging files.
- Pin an upstream Betterleaks version.
- Add license and attribution notes.

Recommended layout:

```text
.
  pyproject.toml
  README.md
  LICENSE
  docs/
  python/
    pybetterleaks/
      __init__.py
      _native.py
      scanner.py
      models.py
      exceptions.py
      native/
        .gitkeep
  bridge/
    go.mod
    go.sum
    bridge.go
  scripts/
    build_native.py
  tests/
    test_models.py
    test_scan_text.py
    test_native_loader.py
  .github/
    workflows/
      wheels.yml
```

Open decisions:

- Package name: `pybetterleaks`, `betterleaks-python`, or another name.
- Import name: recommended `pybetterleaks` unless the package name changes.
- Whether to coordinate naming with Betterleaks maintainers before publishing.

## Phase 1: Minimal Go Bridge Proof Of Concept

Deliverables:

- A `bridge` Go module that depends on a pinned Betterleaks version.
- A C ABI with:
  - `BetterleaksScanJSON(request *C.char) *C.char`
  - `BetterleaksFree(ptr *C.char)`
  - `BetterleaksVersion() *C.char`
- JSON request/response structs for stable cross-language communication.
- Local `go build -buildmode=c-shared` support.

Recommended first scan modes:

- `text`: call Betterleaks detector against an in-memory fragment.
- `dir`: call Betterleaks against a local directory source.

Success criteria:

- The bridge compiles on at least one platform.
- Python can load the compiled library with `ctypes`.
- `scan_text` returns at least one known finding from a fixture.
- The bridge returns structured errors instead of panicking.

Risks:

- Betterleaks internal APIs may change across versions.
- Some Betterleaks constructors may call logging fatal paths instead of
  returning errors. The bridge should isolate and test those paths carefully.
- Directory source construction needs to match Betterleaks' current `sources`
  API, not guesses from the CLI.

## Phase 2: Python Package API

Deliverables:

- `_native.py` to locate and load the platform library.
- `scanner.py` with friendly public functions.
- `models.py` with typed dataclasses or Pydantic models.
- `exceptions.py` for package-specific errors.
- Unit tests for model parsing and error handling.

Recommended API:

```python
from pybetterleaks import scan_dir, scan_text

scan_text("github_pat_example")
scan_dir(".", config_path=".betterleaks.toml", validation=False)
```

Recommended result shape:

```python
@dataclass(frozen=True)
class ScanResult:
    findings: list[Finding]
    errors: list[ScanError]
    betterleaks_version: str | None = None
```

```python
@dataclass(frozen=True)
class Finding:
    rule_id: str
    description: str | None
    file: str | None
    line: int | None
    column: int | None
    secret: str | None
    match: str | None
    validation_status: str | None
    attributes: dict[str, str]
```

Success criteria:

- Importing the package fails clearly when no native library exists.
- Result parsing is deterministic.
- Python users do not see raw C pointers, native memory management, or raw JSON.

## Phase 3: Packaging And Local Build

Deliverables:

- `pyproject.toml` using `setuptools` or another simple backend.
- Package data includes `native/*.so`, `native/*.dylib`, and `native/*.dll`.
- `scripts/build_native.py` builds the shared library into the package data
  directory.
- Source distribution policy is documented.

Recommended build policy:

- Publish wheels as the primary installation path.
- Avoid source builds for production.
- If a source distribution exists, make it require Go and fail loudly if Go is
  missing.
- Recommend production installs use:

```bash
pip install --only-binary=:all: pybetterleaks
```

Success criteria:

- `uv build --wheel` creates a wheel with the native library included after
  `uv run python scripts/build_native.py`.
- `uv build --sdist` creates a source archive without generated native
  libraries.
- Installing that wheel into a clean environment works.
- A smoke test can import the package and scan a fixture.

## Phase 4: CI Wheel Builds

Deliverables:

- GitHub Actions workflow for Linux, macOS, and Windows.
- Go setup in CI.
- Python setup in CI.
- `cibuildwheel` build/test configuration.
- Artifact upload for wheels.

Initial platform target:

- Linux x86_64 manylinux.
- Linux aarch64 manylinux if CI runtime permits it.
- macOS arm64.
- macOS x86_64.
- Windows amd64.

Defer:

- Alpine/musllinux until the Go shared library loader issue is solved.
- Windows arm64.
- PyPy unless there is demand.

Success criteria:

- Every wheel is tested after installation.
- The test command imports `pybetterleaks` and runs `scan_text`.
- Wheels are uploaded as CI artifacts on pull requests.

## Phase 5: Security And Supply Chain

Deliverables:

- Pin Betterleaks version or commit.
- Pin Go module checksums in `go.sum`.
- Use GitHub trusted publishing for PyPI.
- Separate build and publish jobs.
- Generate checksums for wheel artifacts.
- Consider SBOM generation after the first working release.

Rules:

- Do not download native binaries during `pip install`.
- Do not publish wheels built on a developer laptop as the main release path.
- Do not use broad CI secrets on pull request builds.
- Keep release permissions minimal.

## Phase 6: Documentation And Examples

Deliverables:

- User README with install and quickstart.
- Docker example using `python:3.12-slim` or newer.
- API reference.
- Troubleshooting guide.
- Maintainer release checklist.

Example Docker target:

```dockerfile
FROM python:3.12-slim

RUN pip install --only-binary=:all: pybetterleaks

COPY . /app
WORKDIR /app

CMD ["python", "scan.py"]
```

## Phase 7: PyPI Release

Deliverables:

- Reserve and publish package name.
- First pre-release, for example `0.1.0a1`.
- Smoke-test installation from TestPyPI or PyPI.
- Release notes that clearly state the bundled Betterleaks version.

Release checklist:

- Tag repository.
- CI builds all wheels.
- CI tests all wheels.
- Publish via trusted publishing.
- Verify `pip install pybetterleaks` in a clean environment.
- Verify Docker install.
- Update docs with exact supported platforms.

## Phase 8: Post-0.1 Expansion

Potential improvements:

- Add streaming results.
- Add Git source scanning.
- Add GitHub/GitLab/Hugging Face/S3 source scans.
- Add richer validation metadata.
- Add `pybetterleaks validate-config`.
- Add compatibility matrix by Betterleaks version.
- Add benchmarks against Betterleaks CLI.

v0.2 update:

- Typed config, async wrappers, validation env var bridging, checksum tooling,
  and benchmark scaffolding moved from future work into the implementation.
- Musllinux/Alpine remains blocked by the Go/musl `initial-exec TLS` loader
  failure observed during Alpine experiments.
