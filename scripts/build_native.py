from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "bridge"
NATIVE_OUT = ROOT / "python" / "pybetterleaks" / "native"


def lib_name(system: Optional[str] = None) -> str:
    current_system = system or platform.system()
    if current_system == "Linux":
        return "libbetterleaks_py.so"
    if current_system == "Darwin":
        return "libbetterleaks_py.dylib"
    if current_system == "Windows":
        return "betterleaks_py.dll"
    raise RuntimeError(f"Unsupported platform: {current_system}")


def main() -> None:
    if shutil.which("go") is None:
        raise RuntimeError(
            "Go is required to build the PyBetterleaks native bridge. "
            "Install Go or let GitHub Actions build the platform wheels."
        )

    NATIVE_OUT.mkdir(parents=True, exist_ok=True)
    output = NATIVE_OUT / lib_name()

    env = os.environ.copy()
    env["CGO_ENABLED"] = "1"
    if platform.system() == "Darwin":
        env.setdefault("MACOSX_DEPLOYMENT_TARGET", "11.0")
        env["CGO_CFLAGS"] = _append_env_flag(env.get("CGO_CFLAGS"), "-mmacosx-version-min=11.0")
        env["CGO_LDFLAGS"] = _append_env_flag(env.get("CGO_LDFLAGS"), "-mmacosx-version-min=11.0")

    subprocess.check_call(
        [
            "go",
            "build",
            "-trimpath",
            "-buildmode=c-shared",
            "-o",
            str(output),
            ".",
        ],
        cwd=BRIDGE,
        env=env,
    )

    header = output.with_suffix(".h")
    if header.exists():
        header.unlink()

    print(f"Built native library: {output}")


def _append_env_flag(current: Optional[str], flag: str) -> str:
    if not current:
        return flag
    if flag in current.split():
        return current
    return f"{current} {flag}"


if __name__ == "__main__":
    main()
