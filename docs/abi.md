# Native ABI Contract

PyBetterleaks uses a narrow C ABI between Python and the bundled Go shared
library. The ABI should stay stable even if the internal Betterleaks Go API
changes.

## Exported Symbols

```go
BetterleaksScanJSON(requestJSON *C.char) *C.char
BetterleaksCancel(requestID *C.char) *C.char
BetterleaksVersion() *C.char
BetterleaksFree(ptr *C.char)
```

Rules:

- Every returned string is allocated by the Go bridge with `C.CString`.
- Python must call `BetterleaksFree` exactly once for every non-null returned
  pointer.
- All request and response payloads are UTF-8 JSON objects.
- The bridge must recover from panics and return structured errors.
- `BetterleaksCancel` is best-effort. A scan may finish before cancellation
  reaches the registered request id.

## Scan Request

```json
{
  "mode": "text",
  "target": "content or directory path",
  "request_id": "optional-uuid",
  "config_path": null,
  "config_toml": null,
  "validation": false,
  "validation_env_vars": [],
  "validation_env": {},
  "redact": true,
  "timeout_seconds": null
}
```

Fields:

- `mode`: `text` or `dir`.
- `target`: string content for text mode, path for dir mode.
- `request_id`: optional id used by async cancellation.
- `config_path`: optional Betterleaks TOML path for user-owned config files.
- `config_toml`: optional inline Betterleaks TOML. Python typed configs are
  serialized into this field and parsed in Go with Betterleaks'
  `config.ParseTOMLString`.
- `config_path` and `config_toml` are mutually exclusive.
- `validation`: enable Betterleaks validation.
- `validation_env_vars`: allowlisted env var names for validation Expr.
- `validation_env`: values for allowlisted names copied from Python
  `os.environ`.
- `redact`: redact secret values in findings.
- `timeout_seconds`: optional scan deadline.

## Cancel Request

`BetterleaksCancel` receives only a request id string and returns the standard
response envelope. When the request id is active, the bridge cancels the scan
context:

```json
{
  "ok": true,
  "betterleaks_version": "v1.6.1",
  "findings": [],
  "errors": []
}
```

If the scan already finished, the bridge returns `scan_not_found`.

## Response

```json
{
  "ok": true,
  "betterleaks_version": "v1.6.1",
  "findings": [],
  "errors": []
}
```

Error responses keep the same outer shape:

```json
{
  "ok": false,
  "betterleaks_version": "v1.6.1",
  "findings": [],
  "errors": [
    {
      "code": "detector_init_failed",
      "message": "failed to initialize Betterleaks detector",
      "detail": "..."
    }
  ]
}
```

## Finding Shape

The bridge emits snake_case fields:

```json
{
  "rule_id": "github-pat",
  "description": "GitHub personal access token",
  "file": "app.py",
  "line": 12,
  "column": 4,
  "end_line": 12,
  "end_column": 44,
  "secret": "REDACTED",
  "match": "github_pat_...",
  "validation_status": "unknown",
  "validation_meta": {},
  "tags": ["github"],
  "attributes": {},
  "raw": {}
}
```

The Python model parser accepts a few legacy/camel-case aliases, but the native
bridge should produce the canonical snake_case shape.
