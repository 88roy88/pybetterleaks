from pybetterleaks.models import Finding, ScanError, ScanResult


def test_finding_from_native_mapping() -> None:
    finding = Finding.from_mapping(
        {
            "rule_id": "github-pat",
            "description": "GitHub PAT",
            "file": "app.py",
            "line": 12,
            "column": 7,
            "end_line": 12,
            "end_column": 47,
            "secret": "***",
            "match": "github_pat_...",
            "validation_status": "unknown",
            "validation_meta": {"source": "fixture"},
            "tags": ["github", "token"],
            "attributes": {"fingerprint": "abc"},
        }
    )

    assert finding.rule_id == "github-pat"
    assert finding.file == "app.py"
    assert finding.line == 12
    assert finding.tags == ["github", "token"]
    assert finding.attributes["fingerprint"] == "abc"
    assert finding.raw["rule_id"] == "github-pat"


def test_scan_result_from_error_response() -> None:
    result = ScanResult.from_native_response(
        {
            "ok": False,
            "betterleaks_version": "v1.6.1",
            "findings": [],
            "errors": [
                {
                    "code": "config_load_failed",
                    "message": "failed to load config",
                    "detail": "missing.toml",
                }
            ],
        }
    )

    assert not result.ok
    assert result.errors == [
        ScanError(
            code="config_load_failed",
            message="failed to load config",
            detail="missing.toml",
        )
    ]


def test_scan_result_adds_generic_error_when_bridge_reports_failure_without_errors() -> None:
    result = ScanResult.from_native_response(
        {
            "ok": False,
            "betterleaks_version": "v1.6.1",
            "findings": [],
            "errors": [],
        }
    )

    assert not result.ok
    assert result.errors[0].code == "native_error"

