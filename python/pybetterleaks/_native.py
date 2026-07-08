from __future__ import annotations

import ctypes
import json
import os
import platform
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from .exceptions import NativeCallError, NativeLibraryError, NativeLibraryNotFoundError

_ENV_LIBRARY_PATH = "PYBETTERLEAKS_NATIVE_LIBRARY"


def native_library_name(system: Optional[str] = None) -> str:
    current_system = system or platform.system()
    if current_system == "Linux":
        return "libbetterleaks_py.so"
    if current_system == "Darwin":
        return "libbetterleaks_py.dylib"
    if current_system == "Windows":
        return "betterleaks_py.dll"
    raise NativeLibraryError(
        "Unsupported platform for PyBetterleaks native library: "
        f"{current_system or 'unknown'}"
    )


def native_library_path() -> Path:
    override = os.environ.get(_ENV_LIBRARY_PATH)
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / "native" / native_library_name()


@lru_cache(maxsize=1)
def _load_library() -> ctypes.CDLL:
    path = native_library_path()
    if not path.exists():
        raise NativeLibraryNotFoundError(
            path=path,
            system=platform.system(),
            machine=platform.machine(),
        )

    try:
        library = ctypes.CDLL(str(path))
    except OSError as exc:
        raise NativeLibraryError(f"Failed to load native library at {path}: {exc}") from exc

    try:
        library.BetterleaksScanJSON.argtypes = [ctypes.c_char_p]
        library.BetterleaksScanJSON.restype = ctypes.c_void_p
        library.BetterleaksCancel.argtypes = [ctypes.c_char_p]
        library.BetterleaksCancel.restype = ctypes.c_void_p
        library.BetterleaksVersion.argtypes = []
        library.BetterleaksVersion.restype = ctypes.c_void_p
        library.BetterleaksFree.argtypes = [ctypes.c_void_p]
        library.BetterleaksFree.restype = None
    except AttributeError as exc:
        raise NativeLibraryError(
            f"Native library at {path} does not expose the PyBetterleaks ABI"
        ) from exc

    return library


def _decode_owned_string(library: ctypes.CDLL, pointer: int) -> str:
    if not pointer:
        raise NativeCallError("Betterleaks native library returned NULL")

    try:
        return ctypes.string_at(pointer).decode("utf-8")
    finally:
        library.BetterleaksFree(pointer)


def scan_json(payload: Mapping[str, Any]) -> dict[str, Any]:
    library = _load_library()
    request = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    pointer = library.BetterleaksScanJSON(request)
    raw_response = _decode_owned_string(library, pointer)

    try:
        response = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise NativeCallError(
            "Betterleaks native library returned invalid JSON: " f"{raw_response[:200]}"
        ) from exc

    if not isinstance(response, dict):
        raise NativeCallError("Betterleaks native library returned a non-object JSON response")

    return response


def cancel_scan_json(request_id: str) -> dict[str, Any]:
    library = _load_library()
    pointer = library.BetterleaksCancel(request_id.encode("utf-8"))
    raw_response = _decode_owned_string(library, pointer)

    try:
        response = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise NativeCallError(
            "Betterleaks native library returned invalid cancel JSON: "
            f"{raw_response[:200]}"
        ) from exc

    if not isinstance(response, dict):
        raise NativeCallError("Betterleaks native library returned a non-object cancel response")

    return response


def betterleaks_version() -> str:
    library = _load_library()
    pointer = library.BetterleaksVersion()
    version = _decode_owned_string(library, pointer)
    if not version:
        raise NativeCallError("Betterleaks native library returned an empty version")
    return version
