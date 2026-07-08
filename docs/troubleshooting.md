# Troubleshooting

## `NativeLibraryNotFoundError`

The Python package could not find a bundled native library for the current
platform.

For local development:

```bash
uv run python scripts/build_native.py
```

This requires Go on `PATH`.

For production:

```bash
pip install --only-binary=:all: pybetterleaks
```

## `go: command not found`

Install Go locally or rely on GitHub Actions. On macOS:

```bash
brew install go
```

## `uv` touches a user cache outside the sandbox

In restricted environments, use a writable cache:

```bash
uv lock --cache-dir /private/tmp/uv-cache-pybetterleaks
```

In the Codex sandbox, `uv` dependency resolution required escalation because the
network/config layer panicked in the sandboxed macOS environment.

## Wheel Is Tagged `py3-none-any`

Wheels that bundle native libraries must be platform-specific. The project uses
`BinaryDistribution.has_ext_modules()` in `setup.py` to force platform tags.

## Native Bridge Compile Fails After Betterleaks Upgrade

Keep the ABI stable and fix only the Go adapter layer. The Python package should
not expose Betterleaks internal Go structs directly.

## Docker E2E Fails During Build

The E2E image builds a wheel before installing it into the final runtime image.
Docker needs network access to pull the Python base image, install Go in the
builder stage, and download Go/Python build dependencies.

Run the test from the repository root:

```bash
bash e2e/run.sh
```

The final runtime stage should not contain Go. If that assertion fails, check
the Dockerfile stage boundary before trusting the result.

## Alpine E2E Fails With `initial-exec TLS`

`bash e2e/run-alpine.sh` currently fails when Python tries to load the Go
shared library on musl:

```text
initial-exec TLS resolves to dynamic definition
```

This has been reproduced with:

- Go `-buildmode=c-shared`
- Go `-buildmode=c-archive` linked into a musl shared object
- Python `ctypes` loading the library after process startup

This is a Go + musl shared-library loader limitation, not a missing Alpine
package. Do not publish musllinux wheels until this canary passes without
`LD_PRELOAD`, wrapper launchers, or runtime subprocesses.

## Async Cancellation Does Not Stop Instantly

`scan_text_async` and `scan_dir_async` cancel cooperatively. Python cancellation
notifies the Go bridge, and the native scan exits when Betterleaks observes the
cancelled context. Very small scans may finish before the cancellation request
arrives.

## Validation Env Vars Are Missing In Go

Pass the names explicitly:

```python
scan_text(
    "secret",
    validation=True,
    validation_env_vars=["GITHUB_BASE_URL"],
)
```

The Python layer copies values for those names from `os.environ` into the JSON
request. The Go bridge mirrors them into the Go process environment only while
that scan runs.
