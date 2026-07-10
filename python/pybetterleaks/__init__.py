"""Python-native bindings for Betterleaks."""

from ._version import __version__
from .config import BetterleaksConfig, Expr, Extend, RequiredRule, Rule, Validation
from .exceptions import (
    ConfigFormatError,
    NativeCallError,
    NativeLibraryError,
    NativeLibraryNotFoundError,
    PyBetterleaksError,
)
from .models import Finding, ScanError, ScanResult
from .scanner import (
    SUPPORTED_GIT_SCOPES,
    GitScope,
    betterleaks_version,
    scan_dir,
    scan_dir_async,
    scan_git,
    scan_git_async,
    scan_text,
    scan_text_async,
)

__all__ = [
    "SUPPORTED_GIT_SCOPES",
    "BetterleaksConfig",
    "ConfigFormatError",
    "Expr",
    "Extend",
    "Finding",
    "GitScope",
    "NativeCallError",
    "NativeLibraryError",
    "NativeLibraryNotFoundError",
    "PyBetterleaksError",
    "RequiredRule",
    "Rule",
    "ScanError",
    "ScanResult",
    "Validation",
    "__version__",
    "betterleaks_version",
    "scan_dir",
    "scan_dir_async",
    "scan_git",
    "scan_git_async",
    "scan_text",
    "scan_text_async",
]
