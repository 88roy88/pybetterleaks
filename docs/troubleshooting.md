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

Install Go locally or rely on GitHub Actions. This machine was fixed with:

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
a custom `bdist_wheel` command in `setup.py` to force platform tags.

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

The final runtime stage should not contain Go. If that assertion fails, check the
Dockerfile stage boundary before trusting the result.

## Alpine E2E Fails With `initial-exec TLS`

`bash e2e/run-alpine.sh` currently fails when Python tries to load the Go
`c-shared` library on musl:

```text
initial-exec TLS resolves to dynamic definition
```

This is a known Alpine/musllinux blocker for the current `ctypes` plus Go shared
library design. Keep Alpine out of the supported wheel matrix until the canary
passes.
