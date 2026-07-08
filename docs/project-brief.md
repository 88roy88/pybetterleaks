# Project Brief

## Summary

Build a Python package, tentatively named `pybetterleaks`, that exposes
Betterleaks scanning functionality directly from Python without invoking the
Betterleaks CLI through `subprocess` or `popen`.

The desired user experience is:

```bash
pip install pybetterleaks
```

```python
from pybetterleaks import scan_dir, scan_text

findings = scan_dir(".")
```

The final package should be self-contained for common platforms. Users should
not need a Go toolchain, a preinstalled Betterleaks binary, extra system
packages, or install-time binary downloads.

## Why This Project Is Worth Doing

Betterleaks is a fast, modern secrets scanner written in Go. A native Python
package would let Python applications, CI systems, notebooks, internal security
tools, and agent frameworks run Betterleaks scans without shelling out to a CLI.

The Python ecosystem already has many security tools, but a direct binding to
Betterleaks would be useful because:

- Python users get a simple importable scanner API.
- Docker usage becomes simple and repeatable.
- Findings can be returned as Python models instead of parsed process output.
- Security-sensitive runtime behavior avoids shell construction and CLI parsing.
- The native Betterleaks engine remains the source of truth.

## Verified Facts

As of 2026-07-08:

- Betterleaks lives at <https://github.com/betterleaks/betterleaks>.
- The repository is public and MIT licensed.
- The project is written primarily in Go.
- The GitHub repository showed release `v1.6.1` as latest, dated 2026-06-30.
- The repository includes packages such as `detect`, `config`, `sources`, and
  `report`.
- `detect.Detector` exposes library-style scan entry points, including
  `DetectString` and `Run(ctx, source)`.
- `sources.Source` is an interface that yields scan fragments.
- `config.Default()` and `config.LoadFile(...)` can provide scanner
  configuration.
- Go supports `-buildmode=c-shared`, which can produce a shared library callable
  through a C ABI.
- `cibuildwheel` supports building and testing wheels across Linux, macOS, and
  Windows in GitHub Actions.

Primary references:

- Betterleaks repository: <https://github.com/betterleaks/betterleaks>
- Betterleaks detector source:
  <https://raw.githubusercontent.com/betterleaks/betterleaks/main/detect/detect.go>
- Betterleaks config source:
  <https://raw.githubusercontent.com/betterleaks/betterleaks/main/config/config.go>
- Betterleaks source interface:
  <https://raw.githubusercontent.com/betterleaks/betterleaks/main/sources/source.go>
- Go build modes:
  <https://pkg.go.dev/cmd/go#hdr-Build_modes>
- cibuildwheel docs: <https://cibuildwheel.pypa.io/en/stable/>

## Core Decision

Use a small Go bridge compiled as a shared library and call it from Python via
`ctypes` or `cffi`.

Do not build the Python package as a CLI wrapper around `betterleaks`. The user
explicitly rejected a `subprocess`-only wrapper, and that instinct is correct
for an SDK.

## Target Scope

Initial public API:

- `scan_text(text, *, config_path=None, validation=False, redact=True)`
- `scan_dir(path, *, config_path=None, validation=False, redact=True)`
- `betterleaks_version()`
- Typed result models for findings and scan errors.

Later API:

- Git repository scans.
- GitHub/GitLab/Hugging Face/S3 source scans.
- Streaming scan results.
- Async-friendly wrappers.
- Config inspection and rule metadata.

## Non-Goals For Version 0.1

- Reimplementing Betterleaks in Python.
- Automatically generating broad Go-to-Python bindings.
- Matching every Betterleaks CLI option on day one.
- Supporting Alpine/musllinux before manylinux is stable.
- Downloading native binaries during `pip install`.
- Depending on a Betterleaks CLI executable at runtime.

## Local Workspace Notes

At initial documentation creation time, this repository had no source files or
commits. It now contains the Python SDK scaffold, Go bridge, tests, CI
workflows, and a locally built macOS arm64 native library. Go was installed
after the initial scaffold and native smoke tests pass locally.
