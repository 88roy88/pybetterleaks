"""Verify that the bundled Betterleaks version is pinned consistently."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO_MOD = Path("bridge/go.mod")
GO_SUM = Path("bridge/go.sum")
BRIDGE_GO = Path("bridge/bridge.go")

MODULE = "github.com/betterleaks/betterleaks"
GO_SUM_RE = re.compile(r"^h1:[A-Za-z0-9+/]+={0,2}$")


@dataclass(frozen=True)
class ModuleChecksums:
    module: str
    go_mod: str


@dataclass(frozen=True)
class PinState:
    module: str
    version: str
    bridge_version: str
    checksums: ModuleChecksums


EXPECTED_BETTERLEAKS_CHECKSUMS = {
    "v1.6.1": ModuleChecksums(
        module="h1:ZSnqAMwvIudpeHxzbBu8LlAwV/T8Ty2ygrJDtC4IBiQ=",
        go_mod="h1:VxY1tDWcVg0+WNrzM+Qng8zJq7Np5zXAkxOc0/LxCAE=",
    ),
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _go_mod_version(root: Path) -> str:
    path = root / GO_MOD
    text = _read(path)
    match = re.search(rf"^\s*require\s+{re.escape(MODULE)}\s+(v[^\s]+)\s*$", text, re.MULTILINE)
    if not match:
        raise SystemExit(f"{path} does not pin {MODULE}")
    return match.group(1)


def _bridge_version(root: Path) -> str:
    path = root / BRIDGE_GO
    text = _read(path)
    match = re.search(r'const\s+bundledBetterleaksVersion\s+=\s+"([^"]+)"', text)
    if not match:
        raise SystemExit(f"{path} does not declare bundledBetterleaksVersion")
    return match.group(1)


def _go_sum_entries(path: Path) -> dict[tuple[str, str], str]:
    entries: dict[tuple[str, str], str] = {}
    for line_number, line in enumerate(_read(path).splitlines(), start=1):
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) != 3:
            raise SystemExit(f"{path}:{line_number}: invalid go.sum line")

        module, version, checksum = parts
        if module != MODULE:
            continue

        if GO_SUM_RE.fullmatch(checksum) is None:
            raise SystemExit(f"{path}:{line_number}: invalid checksum for {MODULE} {version}")

        key = (module, version)
        existing = entries.get(key)
        if existing is not None and existing != checksum:
            raise SystemExit(f"{path}:{line_number}: conflicting checksum for {MODULE} {version}")
        entries[key] = checksum
    return entries


def _require_go_sum(root: Path, version: str) -> ModuleChecksums:
    expected = EXPECTED_BETTERLEAKS_CHECKSUMS.get(version)
    if expected is None:
        raise SystemExit(
            "No expected Betterleaks checksum is recorded for "
            f"{MODULE} {version}; update scripts/check_betterleaks_pin.py"
        )

    path = root / GO_SUM
    entries = _go_sum_entries(path)
    module_sum = entries.get((MODULE, version))
    go_mod_sum = entries.get((MODULE, f"{version}/go.mod"))

    missing = []
    if module_sum is None:
        missing.append(f"{MODULE} {version}")
    if go_mod_sum is None:
        missing.append(f"{MODULE} {version}/go.mod")
    if missing:
        raise SystemExit(f"{path} is missing checksum line(s): {', '.join(missing)}")

    mismatches = []
    if module_sum != expected.module:
        mismatches.append(f"{MODULE} {version}")
    if go_mod_sum != expected.go_mod:
        mismatches.append(f"{MODULE} {version}/go.mod")
    if mismatches:
        raise SystemExit(
            f"{path} checksum mismatch for {', '.join(mismatches)}; "
            "verify the Betterleaks upgrade intentionally before release"
        )

    return ModuleChecksums(module=module_sum, go_mod=go_mod_sum)


def check_pin(root: Path = ROOT) -> PinState:
    go_mod_version = _go_mod_version(root)
    bridge_version = _bridge_version(root)

    if go_mod_version != bridge_version:
        raise SystemExit(
            "Betterleaks version mismatch: "
            f"go.mod requires {go_mod_version}, bridge reports {bridge_version}"
        )

    checksums = _require_go_sum(root, go_mod_version)
    return PinState(
        module=MODULE,
        version=go_mod_version,
        bridge_version=bridge_version,
        checksums=checksums,
    )


def main() -> None:
    state = check_pin()
    print(
        "Betterleaks pin OK: "
        f"{state.module} {state.version} "
        f"(module {state.checksums.module}, go.mod {state.checksums.go_mod})"
    )


if __name__ == "__main__":
    main()
