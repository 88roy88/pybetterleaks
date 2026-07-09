import asyncio
import threading
from pathlib import Path

import pytest
from pybetterleaks import BetterleaksConfig, Rule, scanner


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
        "git_scope": None,
        "request_id": None,
        "config_path": None,
        "config_toml": None,
        "validation": True,
        "validation_env_vars": [],
        "validation_env": {},
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
    assert captured["git_scope"] is None
    assert captured["config_path"] == str(config_path)
    assert captured["config_toml"] is None
    assert result.ok


def test_scan_text_serializes_validation_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}
    monkeypatch.setenv("PYBETTERLEAKS_BASE_URL", "https://betterleaks.invalid")

    def fake_scan_json(payload):
        captured.update(payload)
        return {
            "ok": True,
            "betterleaks_version": "v1.6.1",
            "findings": [],
            "errors": [],
        }

    monkeypatch.setattr(scanner, "_native_scan_json", fake_scan_json)

    scanner.scan_text("secret", validation=True, validation_env_vars=["PYBETTERLEAKS_BASE_URL"])

    assert captured["validation_env_vars"] == ["PYBETTERLEAKS_BASE_URL"]
    assert captured["validation_env"] == {
        "PYBETTERLEAKS_BASE_URL": "https://betterleaks.invalid"
    }


def test_scan_git_serializes_worktree_scope(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured = {}

    def fake_scan_json(payload):
        captured.update(payload)
        return {
            "ok": True,
            "betterleaks_version": "v1.6.1",
            "findings": [],
            "errors": [],
        }

    monkeypatch.setattr(scanner, "_native_scan_json", fake_scan_json)

    result = scanner.scan_git(tmp_path)

    assert result.ok
    assert captured["mode"] == "git"
    assert captured["target"] == str(tmp_path)
    assert captured["git_scope"] == "worktree"
    assert scanner.SUPPORTED_GIT_SCOPES == ("worktree",)


def test_scan_text_serializes_typed_config_toml(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}
    config = BetterleaksConfig(
        rules=[
            Rule(
                id="typed-config",
                description="Typed config",
                regex=r"TYPED_CONFIG_[A-Z0-9]{16}",
                keywords=["TYPED_CONFIG_"],
            )
        ]
    )

    def fake_scan_json(payload):
        captured.update(payload)
        return {
            "ok": True,
            "betterleaks_version": "v1.6.1",
            "findings": [],
            "errors": [],
        }

    monkeypatch.setattr(scanner, "_native_scan_json", fake_scan_json)

    result = scanner.scan_text("TYPED_CONFIG_0123456789ABCDEF", config=config)

    assert result.ok
    assert captured["config_path"] is None
    assert "typed-config" in str(captured["config_toml"])


def test_scan_rejects_config_and_config_path(tmp_path: Path) -> None:
    config = BetterleaksConfig(
        rules=[
            Rule(
                id="typed-config",
                description="Typed config",
                regex=r"TYPED_CONFIG_[A-Z0-9]{16}",
            )
        ]
    )

    with pytest.raises(ValueError, match="mutually exclusive"):
        scanner.scan_text("secret", config=config, config_path=tmp_path / "betterleaks.toml")


def test_scan_rejects_non_positive_timeout() -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        scanner.scan_text("secret", timeout_seconds=0)


def test_scan_git_rejects_unsupported_scope(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="scope"):
        scanner.scan_git(tmp_path, scope="tracked")  # type: ignore[arg-type]


def test_scan_text_async_serializes_request_id(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_scan_json(payload):
        captured.update(payload)
        return {
            "ok": True,
            "betterleaks_version": "v1.6.1",
            "findings": [],
            "errors": [],
        }

    monkeypatch.setattr(scanner, "_native_scan_json", fake_scan_json)

    result = asyncio.run(scanner.scan_text_async("secret"))

    assert result.ok
    assert captured["request_id"]


def test_scan_text_async_cancels_native_request(monkeypatch: pytest.MonkeyPatch) -> None:
    started = threading.Event()
    release = threading.Event()
    captured_request_id = ""
    cancelled_request_ids = []

    def fake_scan_text(*args, **kwargs):
        nonlocal captured_request_id
        captured_request_id = str(kwargs["_request_id"])
        started.set()
        release.wait(timeout=5)
        return scanner.ScanResult(
            findings=[],
            errors=[],
            betterleaks_version="v1.6.1",
        )

    def fake_cancel_scan_json(request_id: str):
        cancelled_request_ids.append(request_id)
        return {"ok": True, "betterleaks_version": "v1.6.1", "findings": [], "errors": []}

    async def run_cancelled_scan() -> None:
        task = asyncio.create_task(scanner.scan_text_async("secret"))
        await asyncio.to_thread(started.wait, 5)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            release.set()

    monkeypatch.setattr(scanner, "scan_text", fake_scan_text)
    monkeypatch.setattr(scanner, "_native_cancel_scan_json", fake_cancel_scan_json)

    asyncio.run(run_cancelled_scan())

    assert cancelled_request_ids == [captured_request_id]
