# PyBetterleaks E2E

This directory contains Docker end-to-end tests for the packaged SDK.

The default test uses two stages:

1. A Python builder stage installs Go, builds the native bridge, and creates a
   local wheel.
2. A final Python runtime stage installs that wheel from `/tmp` with
   `pip --no-index`, then runs the SDK against fixture files.

The final stage intentionally has no Go toolchain. That checks the production
promise: users install a wheel and import Python, with no Betterleaks CLI and no
runtime subprocess.

Run the runtime-wheel E2E from the repository root:

```bash
bash e2e/run.sh
```

The runner checks:

- `betterleaks_version()`
- `scan_text()` with a TOML config path
- `scan_text()` with a typed `BetterleaksConfig`
- `scan_text_async()` with a typed `BetterleaksConfig`
- `scan_dir()` over nested fixture files
- `scan_git()` over a synthetic local worktree
- structured native errors
- timeout input validation
- no Go runtime in the final image

Alpine/musllinux is not a supported runtime. Previous experiments exposed a
known Go + musl loader blocker for Go shared libraries loaded through Python
`ctypes`:

```text
initial-exec TLS resolves to dynamic definition
```

No Alpine E2E path is maintained. Revisit musllinux only with a fresh loader
proof that does not require `LD_PRELOAD`, wrapper launchers, or runtime
subprocesses.

The fixtures use fake secrets only. They are shaped to trigger Betterleaks rules
without representing real credentials.
