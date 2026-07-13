# Git Scanning

`scan_git` scans a local Git worktree through the bundled Betterleaks engine.
It does not invoke the `git` executable.

```python
from pybetterleaks import SUPPORTED_GIT_SCOPES, scan_git

print(SUPPORTED_GIT_SCOPES)

result = scan_git(
    ".",
    scope="worktree",
    config_path=".betterleaks.toml",
    redact=True,
    raise_on_error=True,
)

for finding in result.findings:
    print(f"{finding.file}:{finding.line} {finding.rule_id}")
```

## Supported Scope

The supported scope is intentionally explicit:

```python
from pybetterleaks import SUPPORTED_GIT_SCOPES

assert SUPPORTED_GIT_SCOPES == ("worktree",)
```

`scope="worktree"` means:

- the target path must be inside a Git worktree
- files under `.git` are skipped
- untracked files in the worktree can be scanned
- Git history, staged-only changes, and diffs are not scanned

## Why Only Worktree Today?

PyBetterleaks promises no runtime `subprocess` for supported APIs. Upstream
Betterleaks supports richer Git sources, but history and diff workflows commonly
depend on Git plumbing. PyBetterleaks keeps the v0.x Git API honest by exposing
only the scope it can support without shelling out.

Future scopes are tracked in the repo backlog:

- `tracked`
- `staged`
- `diff`
- `history`

Those scopes need either a pure-Go implementation path or an explicit product
decision to allow an optional subprocess-backed mode.

## Typed Config

Git scans accept the same config inputs as text and directory scans:

```python
from pybetterleaks import BetterleaksConfig, Rule, scan_git

config = BetterleaksConfig(
    rules=[
        Rule.prefixed_token_rule(
            id="internal-token",
            description="Internal service token",
            prefix="INTERNAL_",
            token_pattern=r"[A-Z0-9]{16}",
        )
    ]
)

result = scan_git(".", config=config, scope="worktree")
```

Do not pass both `config` and `config_path`.

## Async Worktree Scan

```python
import asyncio
from pybetterleaks import scan_git_async


async def main() -> None:
    result = await scan_git_async(".", scope="worktree", timeout_seconds=10)
    print(result.ok, len(result.findings))


asyncio.run(main())
```

Cancelling the Python task requests cooperative cancellation from the native Go
bridge. Cancellation is best-effort: the async task is cancelled immediately,
while the native scan is asked to stop as soon as the bridge can observe the
request.

## Errors

By default, expected scan failures are returned in `result.errors`:

```python
from pybetterleaks import scan_git

result = scan_git("/not/a/repo")
for error in result.errors:
    print(error.code, error.message)
```

Use `raise_on_error=True` when exception-style control flow is more convenient:

```python
from pybetterleaks import ScanFailedError, scan_git

try:
    scan_git("/not/a/repo", raise_on_error=True)
except ScanFailedError as exc:
    print(exc.code)
```
