from pathlib import Path

import pytest
from pybetterleaks import scanner


def test_scan_text_serializes_request(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_scan_json(payload):
        captured.update(payload)
        return {
            "ok": True,
            "betterleaks_version": "v1.6.1",
            "findings": [{"rule_id": "fixture", "line": 1}],
            "errors": [],
        }

    monkeypatch.setattr(scanner, "_native_scan_json", fake_scan_json)

    result = scanner.scan_text("secret", validation=True, redact=False, timeout_seconds=1.5)

    assert captured == {
        "mode": "text",
        "target": "secret",
        "config_path": None,
        "validation": True,
        "redact": False,
        "timeout_seconds": 1.5,
    }
    assert result.findings[0].rule_id == "fixture"


def test_scan_dir_serializes_path_inputs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured = {}
    config_path = tmp_path / ".betterleaks.toml"

    def fake_scan_json(payload):
        captured.update(payload)
        return {
            "ok": True,
            "betterleaks_version": "v1.6.1",
            "findings": [],
            "errors": [],
        }

    monkeypatch.setattr(scanner, "_native_scan_json", fake_scan_json)

    result = scanner.scan_dir(tmp_path, config_path=config_path)

    assert captured["mode"] == "dir"
    assert captured["target"] == str(tmp_path)
    assert captured["config_path"] == str(config_path)
    assert result.ok


def test_scan_rejects_non_positive_timeout() -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        scanner.scan_text("secret", timeout_seconds=0)

