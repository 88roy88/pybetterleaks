"""Python-native bindings for Betterleaks."""

from ._version import __version__
from .exceptions import (
    NativeCallError,
    NativeLibraryError,
    NativeLibraryNotFoundError,
    PyBetterleaksError,
)
from .models import Finding, ScanError, ScanResult
from .scanner import betterleaks_version, scan_dir, scan_text

__all__ = [
    "Finding",
    "NativeCallError",
    "NativeLibraryError",
    "NativeLibraryNotFoundError",
    "PyBetterleaksError",
    "ScanError",
    "ScanResult",
    "__version__",
    "betterleaks_version",
    "scan_dir",
    "scan_text",
]

