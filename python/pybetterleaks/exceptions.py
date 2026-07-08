from __future__ import annotations

from pathlib import Path


class PyBetterleaksError(Exception):
    """Base exception for PyBetterleaks errors."""


class NativeLibraryError(PyBetterleaksError):
    """Raised when the native Betterleaks bridge cannot be used."""


class NativeLibraryNotFoundError(NativeLibraryError):
    """Raised when no bundled native library exists for the current platform."""

    def __init__(self, *, path: Path, system: str, machine: str) -> None:
        self.path = path
        self.system = system
        self.machine = machine
        super().__init__(
            "Missing bundled Betterleaks native library for "
            f"{system or 'unknown'} {machine or 'unknown'}: {path}. "
            "Build it with `uv run python scripts/build_native.py` or install a "
            "wheel matching this platform."
        )


class NativeCallError(NativeLibraryError):
    """Raised when a native call fails before a structured scan response exists."""
