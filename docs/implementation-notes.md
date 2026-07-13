# Implementation Notes

## Package Backend

Start with `setuptools`. This project is not a normal CPython extension module;
it is a pure Python package that includes a prebuilt Go shared library as
package data.

Initial `pyproject.toml` direction:

```toml
[build-system]
requires = ["setuptools>=70", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pybetterleaks"
version = "0.6.1"
description = "Native Python bindings for Betterleaks"
readme = "README.md"
requires-python = ">=3.9"
license = { text = "MIT" }

[tool.setuptools]
package-dir = {"" = "python"}

[tool.setuptools.packages.find]
where = ["python"]

[tool.setuptools.package-data]
pybetterleaks = [
  "py.typed",
  "native/*.so",
  "native/*.dylib",
  "native/*.dll",
]
```

The actual metadata should be refined before publishing.

## Wheel Tags

Because the package contains native libraries, wheels are platform-specific.
The Python code can remain pure, but the distribution artifact cannot be a
universal pure Python wheel.

Potential wheel target:

```text
pybetterleaks-0.5.0-py3-none-manylinux_2_28_x86_64.whl
pybetterleaks-0.5.0-py3-none-manylinux_2_28_aarch64.whl
pybetterleaks-0.5.0-py3-none-macosx_11_0_arm64.whl
pybetterleaks-0.5.0-py3-none-macosx_11_0_x86_64.whl
pybetterleaks-0.5.0-py3-none-win_amd64.whl
```

If the build backend emits CPython-specific tags such as `cp312-cp312`, that is
acceptable for an early version but creates more wheels to build. Prefer
Python-version-independent platform wheels if practical.

## Native Build Script

The native build script should:

- Detect platform.
- Create `python/pybetterleaks/native/`.
- Run `go build -trimpath -buildmode=c-shared`.
- Remove generated header files from package data unless needed.
- Print the final library path.

The script may use `subprocess` at build time. The no-subprocess requirement is
for package runtime behavior.

## Go Bridge Rules

Keep the bridge narrow:

- Export only a few C symbols.
- Convert all inputs and outputs through JSON.
- Recover from panics and return structured errors.
- Never return Go-owned memory directly without a matching free function.
- Avoid global mutable state unless it is deliberate and protected.
- Keep Betterleaks version pin explicit in `go.mod`.
- Keep `docs/betterleaks-pin.md` aligned with `bridge/go.mod`.
- Run `uv run python scripts/check_betterleaks_pin.py` in CI so the module pin,
  `go.sum`, and the runtime version constant cannot drift.

Memory rule:

- Every string allocated with `C.CString` must be freed by Python calling
  `BetterleaksFree`.

## Error Handling

The bridge should never crash Python for expected errors such as:

- Invalid JSON request.
- Unsupported scan mode.
- Missing config file.
- Invalid config.
- Missing target path.
- Betterleaks scan error.
- Timeout/cancellation.

Return structured errors in JSON and let Python raise a friendly exception only
when the native layer itself cannot be loaded or called.

## Testing Strategy

Python-only tests:

- Model parsing.
- Request serialization.
- Error response handling.
- Missing native library message.
- Platform library name detection.

Native smoke tests:

- Load native library.
- Call `betterleaks_version()`.
- `scan_text` fixture with known fake secret.
- `scan_dir` fixture directory.
- Typed config fixture.
- Validation env var fixture.
- Config load success/failure.

Wheel tests:

- Install the built wheel into a clean virtual environment.
- Import `pybetterleaks`.
- Run `scan_text`.
- Exercise typed config and async wrappers.
- Confirm the native library path is inside the installed package.

## Fixtures

Use obviously fake secrets that match Betterleaks rules but are not valid
credentials. Do not commit real keys or real-looking private credentials.

If a fixture uses a token-like string, document that it is fake and keep it
non-operational.

## Docker Compatibility

Prioritize Debian/Ubuntu style images first:

```dockerfile
FROM python:3.12-slim

RUN pip install --only-binary=:all: pybetterleaks
```

Alpine/musllinux is unsupported in v0.2 and remains blocked by the current Go +
musl shared-library loader failure:

```text
initial-exec TLS resolves to dynamic definition
```

Do not publish musllinux wheels without a clean loader proof that avoids runtime
launch workarounds.

## Source Distribution Policy

For now, publish wheels only. `MANIFEST.in` excludes generated native libraries
from sdists so a developer-machine macOS dylib cannot accidentally land in a
source archive. Local wheel builds must use `uv build --wheel` after running
`uv run python scripts/build_native.py`; plain combined builds may build the
wheel from the sdist and therefore omit the native library.

## Supply Chain Notes

This is a security scanner, so release hygiene matters.

Recommended:

- Use GitHub trusted publishing for PyPI.
- Separate build and publish jobs.
- Pin Betterleaks versions.
- Commit `go.sum`.
- Upload checksums for wheels.
- Verify checksums before publishing.
- Attach checksums to GitHub releases.
- Create GitHub artifact attestations for release artifacts.
- Run smoke tests against installed wheels.
- Avoid install-time downloads.
- Avoid storing PyPI tokens if trusted publishing is available.
- Defer automated SBOM generation until the source-build story is stable or the
  project approaches `1.0.0`.

## Naming Notes

Before publishing, check PyPI name availability and consider contacting
Betterleaks maintainers if using a name that implies official ownership.

Possible names:

- `pybetterleaks`
- `betterleaks-python`
- `betterleaks-py`

`pybetterleaks` is clear and leaves room for an official `betterleaks` package
if maintainers later want that name.

## Local Toolchain Notes

The local machine initially did not have Go installed. Go was later installed
with Homebrew and reported `go1.26.5 darwin/arm64`. The macOS arm64 native
bridge build and native smoke tests now pass locally.

CI should remain the release source of truth for Linux, macOS, and Windows
wheels.
