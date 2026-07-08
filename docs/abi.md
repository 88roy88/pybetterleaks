# Native ABI Contract

PyBetterleaks uses a narrow C ABI between Python and the bundled Go shared
library. The ABI should stay stable even if the internal Betterleaks Go API
changes.

## Exported Symbols

```go
BetterleaksScanJSON(requestJSON *C.char) *C.char
BetterleaksVersion() *C.char
BetterleaksFree(ptr *C.char)
```

Rules:

- Every returned string is allocated by the Go bridge with `C.CString`.
- Python must call `BetterleaksFree` exactly once for every non-null returned
  pointer.
- All request and response payloads are UTF-8 JSON objects.
- The bridge must recover from panics and return structured errors.

## Request

```json
{
  "mode": "text",
  "target": "content or directory path",
  "config_path": null,
  "validation": false,
  "redact": true,
  "timeout_seconds": null
}
```

Supported `mode` values for v0.1:

- `text`
- `dir`

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
      "code": "config_load_failed",
      "message": "failed to load config",
      "detail": "..."
    }
  ]
}
```

## Finding Shape

The bridge should emit snake_case fields:

```json
{
  "rule_id": "github-pat",
  "description": "GitHub personal access token",
  "file": "app.py",
  "line": 12,
  "column": 4,
  "end_line": 12,
  "end_column": 44,
  "secret": "***",
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

