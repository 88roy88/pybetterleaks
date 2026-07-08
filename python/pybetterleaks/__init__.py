"""Python-native bindings for Betterleaks."""

from ._version import __version__
from .config import BetterleaksConfig, Expr, Extend, RequiredRule, Rule
from .exceptions import (
    ConfigFormatError,
    NativeCallError,
    NativeLibraryError,
    NativeLibraryNotFoundError,
    PyBetterleaksError,
)
from .models import Finding, ScanError, ScanResult
from .scanner import (
    betterleaks_version,
    scan_dir,
    scan_dir_async,
    scan_git,
    scan_git_async,
    scan_text,
    scan_text_async,
)

__all__ = [
    "BetterleaksConfig",
    "ConfigFormatError",
    "Expr",
    "Extend",
    "Finding",
    "NativeCallError",
    "NativeLibraryError",
    "NativeLibraryNotFoundError",
    "PyBetterleaksError",
    "RequiredRule",
    "Rule",
    "ScanError",
    "ScanResult",
    "__version__",
    "betterleaks_version",
    "scan_dir",
    "scan_dir_async",
    "scan_git",
    "scan_git_async",
    "scan_text",
    "scan_text_async",
]
