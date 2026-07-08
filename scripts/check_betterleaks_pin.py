"""Verify that the bundled Betterleaks version is pinned consistently."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "bridge"
GO_MOD = BRIDGE / "go.mod"
GO_SUM = BRIDGE / "go.sum"
BRIDGE_GO = BRIDGE / "bridge.go"

MODULE = "github.com/betterleaks/betterleaks"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _go_mod_version() -> str:
    text = _read(GO_MOD)
    match = re.search(rf"^\s*require\s+{re.escape(MODULE)}\s+(v[^\s]+)\s*$", text, re.MULTILINE)
    if not match:
        raise SystemExit(f"{GO_MOD} does not pin {MODULE}")
    return match.group(1)


def _bridge_version() -> str:
    text = _read(BRIDGE_GO)
    match = re.search(r'const\s+bundledBetterleaksVersion\s+=\s+"([^"]+)"', text)
    if not match:
        raise SystemExit(f"{BRIDGE_GO} does not declare bundledBetterleaksVersion")
    return match.group(1)


def _require_go_sum(version: str) -> None:
    text = _read(GO_SUM)
    module_line = f"{MODULE} {version} "
    mod_line = f"{MODULE} {version}/go.mod "
    missing = [line for line in (module_line, mod_line) if line not in text]
    if missing:
        raise SystemExit(f"{GO_SUM} is missing checksum lines for {MODULE} {version}")


def main() -> None:
    go_mod_version = _go_mod_version()
    bridge_version = _bridge_version()

    if go_mod_version != bridge_version:
        raise SystemExit(
            "Betterleaks version mismatch: "
            f"go.mod requires {go_mod_version}, bridge reports {bridge_version}"
        )

    _require_go_sum(go_mod_version)
    print(f"Betterleaks pin OK: {MODULE} {go_mod_version}")


if __name__ == "__main__":
    main()
