from __future__ import annotations

from pathlib import Path

import pytest

from scripts import check_betterleaks_pin

MODULE = check_betterleaks_pin.MODULE
EXPECTED = check_betterleaks_pin.EXPECTED_BETTERLEAKS_CHECKSUMS["v1.6.1"]


def test_check_pin_accepts_expected_betterleaks_checksums(tmp_path: Path) -> None:
    write_pin_fixture(tmp_path)

    state = check_betterleaks_pin.check_pin(tmp_path)

    assert state.module == MODULE
    assert state.version == "v1.6.1"
    assert state.bridge_version == "v1.6.1"
    assert state.checksums == EXPECTED


def test_check_pin_rejects_bridge_version_drift(tmp_path: Path) -> None:
    write_pin_fixture(tmp_path, bridge_version="v1.6.2")

    with pytest.raises(SystemExit, match="version mismatch"):
        check_betterleaks_pin.check_pin(tmp_path)


def test_check_pin_rejects_missing_module_checksum(tmp_path: Path) -> None:
    write_pin_fixture(tmp_path, include_module_sum=False)

    with pytest.raises(SystemExit, match="missing checksum line"):
        check_betterleaks_pin.check_pin(tmp_path)


def test_check_pin_rejects_changed_module_checksum(tmp_path: Path) -> None:
    write_pin_fixture(tmp_path, module_sum="h1:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")

    with pytest.raises(SystemExit, match="checksum mismatch"):
        check_betterleaks_pin.check_pin(tmp_path)


def test_check_pin_rejects_unknown_betterleaks_version_without_expected_sum(
    tmp_path: Path,
) -> None:
    write_pin_fixture(
        tmp_path,
        go_mod_version="v9.9.9",
        bridge_version="v9.9.9",
        module_sum=EXPECTED.module,
        go_mod_sum=EXPECTED.go_mod,
    )

    with pytest.raises(SystemExit, match="No expected Betterleaks checksum"):
        check_betterleaks_pin.check_pin(tmp_path)


def write_pin_fixture(
    root: Path,
    *,
    go_mod_version: str = "v1.6.1",
    bridge_version: str = "v1.6.1",
    module_sum: str = EXPECTED.module,
    go_mod_sum: str = EXPECTED.go_mod,
    include_module_sum: bool = True,
) -> None:
    bridge = root / "bridge"
    bridge.mkdir()
    (bridge / "go.mod").write_text(
        "\n".join(
            [
                "module example.test/bridge",
                "",
                "go 1.25.0",
                "",
                f"require {MODULE} {go_mod_version}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (bridge / "bridge.go").write_text(
        f'package main\n\nconst bundledBetterleaksVersion = "{bridge_version}"\n',
        encoding="utf-8",
    )
    go_sum_lines = []
    if include_module_sum:
        go_sum_lines.append(f"{MODULE} {go_mod_version} {module_sum}")
    go_sum_lines.append(f"{MODULE} {go_mod_version}/go.mod {go_mod_sum}")
    (bridge / "go.sum").write_text("\n".join(go_sum_lines) + "\n", encoding="utf-8")
