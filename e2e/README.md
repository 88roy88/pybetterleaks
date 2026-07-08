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

Run the passing runtime-wheel E2E from the repository root:

```bash
bash e2e/run.sh
```

There is also an Alpine canary:

```bash
bash e2e/run-alpine.sh
```

That canary currently exposes a known musl loader blocker for Go `c-shared`
libraries loaded through Python `ctypes`: Alpine fails with an
`initial-exec TLS resolves to dynamic definition` relocation error before the SDK
can scan. Keep it as a concrete reproduction for future musllinux work; do not
treat Alpine as a supported runtime until that canary passes.

The fixtures use fake secrets only. They are shaped to trigger Betterleaks rules
without representing real credentials.
