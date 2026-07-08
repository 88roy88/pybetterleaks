from pathlib import Path

import pytest
from pybetterleaks import _native
from pybetterleaks.scanner import scan_dir, scan_text

FIXTURES = Path(__file__).resolve().parents[1] / "e2e" / "fixtures"
FIXTURE_CONFIG = FIXTURES / "betterleaks.toml"
FAKE_ALPHA_SECRET = "PYBETTERLEAKS_ALPHA_0A1B2C3D4E5F6A7B"


@pytest.mark.native
def test_native_version_when_library_is_available() -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    assert _native.betterleaks_version().startswith("v")


@pytest.mark.native
def test_native_scan_text_when_library_is_available() -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    result = scan_text(FAKE_ALPHA_SECRET, config_path=FIXTURE_CONFIG)

    assert result.betterleaks_version.startswith("v")
    assert result.ok
    assert len(result.findings) == 1
    assert result.findings[0].rule_id == "pybetterleaks-alpha"
    assert result.findings[0].secret == "REDACTED"


@pytest.mark.native
def test_native_scan_dir_when_library_is_available() -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    result = scan_dir(FIXTURES, config_path=FIXTURE_CONFIG)

    assert result.ok
    rule_ids = {finding.rule_id for finding in result.findings}
    assert {
        "pybetterleaks-alpha",
        "pybetterleaks-beta",
        "pybetterleaks-gamma",
        "pybetterleaks-delta",
    } <= rule_ids
    assert all(finding.file for finding in result.findings)
    assert all(finding.secret == "REDACTED" for finding in result.findings)


@pytest.mark.native
def test_native_invalid_config_returns_structured_error_when_library_is_available() -> None:
    if not _native.native_library_path().exists():
        pytest.skip("native library has not been built")

    result = scan_text(FAKE_ALPHA_SECRET, config_path=FIXTURES / "missing-betterleaks.toml")

    assert not result.ok
    assert result.errors
    assert result.errors[0].code == "detector_init_failed"
