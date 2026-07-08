# Architecture

## High-Level Design

The package should have three layers:

```text
Python application
  -> pybetterleaks Python API
    -> ctypes/cffi native loader
      -> Go shared library bridge
        -> Betterleaks Go packages
```

The Python package should own the user-facing API. The Go bridge should be
small, stable, and boring. Betterleaks should remain the scanning engine.

## Why A JSON C ABI

Go can export functions from a `main` package when built with
`-buildmode=c-shared`. The exported C ABI should stay tiny. Passing rich nested
data structures over C directly would create unnecessary memory-management and
compatibility complexity.

Recommended exported functions:

```go
//export BetterleaksScanJSON
func BetterleaksScanJSON(requestJSON *C.char) *C.char

//export BetterleaksFree
func BetterleaksFree(ptr *C.char)

//export BetterleaksVersion
func BetterleaksVersion() *C.char
```

The bridge receives one UTF-8 JSON request and returns one UTF-8 JSON response.
Python parses the response into typed models.

## Native Request Shape

Initial request:

```json
{
  "mode": "text",
  "target": "secret text or path",
  "config_path": null,
  "validation": false,
  "redact": true,
  "timeout_seconds": null
}
```

Fields:

- `mode`: initially `text` or `dir`.
- `target`: string content for text mode, path for dir mode.
- `config_path`: optional Betterleaks config path.
- `validation`: enable Betterleaks validation when supported.
- `redact`: redact secret values in findings when possible.
- `timeout_seconds`: optional scan deadline.

## Native Response Shape

Initial response:

```json
{
  "ok": true,
  "betterleaks_version": "v1.6.1",
  "findings": [],
  "errors": []
}
```

Error response:

```json
{
  "ok": false,
  "betterleaks_version": "v1.6.1",
  "findings": [],
  "errors": [
    {
      "code": "config_load_failed",
      "message": "failed to load config",
      "detail": "..."
    }
  ]
}
```

## Finding Model

The Python model should preserve enough Betterleaks data to be useful without
locking the API to every internal field.

Recommended fields:

- `rule_id`
- `description`
- `file`
- `line`
- `column`
- `end_line`
- `end_column`
- `secret`
- `match`
- `validation_status`
- `validation_meta`
- `tags`
- `attributes`
- `raw`

`raw` can hold additional Betterleaks fields for forward compatibility.

## Python Loader

The native loader should:

- Detect OS and CPU architecture.
- Locate the packaged library in `pybetterleaks/native/`.
- Load it with `ctypes.CDLL`.
- Set `argtypes` and `restype`.
- Always call `BetterleaksFree` for allocated native responses.
- Raise a clear exception when a native library is missing.

Expected library names:

```text
Linux:   libbetterleaks_py.so
macOS:   libbetterleaks_py.dylib
Windows: betterleaks_py.dll
```

## Public Python API

Recommended initial module exports:

```python
from pybetterleaks import (
    Finding,
    ScanError,
    ScanResult,
    betterleaks_version,
    scan_dir,
    scan_text,
)
```

Recommended functions:

```python
def scan_text(
    text: str,
    *,
    config_path: str | None = None,
    validation: bool = False,
    redact: bool = True,
    timeout_seconds: float | None = None,
) -> ScanResult: ...
```

```python
def scan_dir(
    path: str,
    *,
    config_path: str | None = None,
    validation: bool = False,
    redact: bool = True,
    timeout_seconds: float | None = None,
) -> ScanResult: ...
```

## Build Model

Build-time:

- GitHub Actions installs Go.
- `scripts/build_native.py` compiles `bridge` with `go build`.
- The native library is copied into `python/pybetterleaks/native/`.
- Python wheel build packages that native library as package data.
- `cibuildwheel` tests the built wheel in a clean environment.

Runtime:

- User imports Python package.
- Python loads bundled native library.
- Python sends JSON scan request to native library.
- Native library calls Betterleaks packages directly.
- Native library returns JSON scan result.

No runtime subprocess is required.

## CI Architecture

Recommended workflow jobs:

1. `lint`: Python formatting, type checks, and lightweight tests that do not
   require the native library.
2. `build-wheels`: matrix over OS and architecture, builds native library and
   wheel with `cibuildwheel`.
3. `publish`: runs only on release tags and publishes with trusted publishing.

Keep publishing separate from PR builds.

## Versioning

There are two versions to track:

- Python package version, for example `0.1.0`.
- Bundled Betterleaks version, for example `v1.6.1`.

Expose both:

```python
import pybetterleaks

print(pybetterleaks.__version__)
print(pybetterleaks.betterleaks_version())
```

Release notes should always say which Betterleaks version is bundled.

## Future Architecture

Possible later additions:

- Streaming native callback API for large scans.
- Separate library builds per source family if binary size becomes an issue.
- Async Python API using `asyncio.to_thread`.
- CLI helper for Python users, separate from the Betterleaks CLI.
- Optional extras for Pydantic models or rich output.

