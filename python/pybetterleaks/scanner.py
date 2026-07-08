from __future__ import annotations

import os
from typing import Optional, Union

from ._native import betterleaks_version as _native_betterleaks_version
from ._native import scan_json as _native_scan_json
from .models import ScanResult

PathInput = Union[str, os.PathLike[str]]


def scan_text(
    text: str,
    *,
    config_path: Optional[PathInput] = None,
    validation: bool = False,
    redact: bool = True,
    timeout_seconds: Optional[float] = None,
) -> ScanResult:
    """Scan an in-memory text fragment for secrets.

    Args:
        text: Text content to scan.
        config_path: Optional path to a Betterleaks configuration file.
        validation: Enable Betterleaks validation when supported by the rule.
        redact: Replace secret values in findings with `REDACTED`.
        timeout_seconds: Optional positive scan deadline in seconds.

    Returns:
        A typed scan result containing findings, structured native errors, and
        the bundled Betterleaks version.

    Raises:
        ValueError: If `timeout_seconds` is not positive.
        NativeLibraryError: If the native library cannot load or returns malformed data.
    """
    payload = _scan_payload(
        mode="text",
        target=text,
        config_path=config_path,
        validation=validation,
        redact=redact,
        timeout_seconds=timeout_seconds,
    )
    return ScanResult.from_native_response(_native_scan_json(payload))


def scan_dir(
    path: PathInput,
    *,
    config_path: Optional[PathInput] = None,
    validation: bool = False,
    redact: bool = True,
    timeout_seconds: Optional[float] = None,
) -> ScanResult:
    """Scan a directory with the bundled Betterleaks engine.

    Args:
        path: Directory path to scan.
        config_path: Optional path to a Betterleaks configuration file.
        validation: Enable Betterleaks validation when supported by the rule.
        redact: Replace secret values in findings with `REDACTED`.
        timeout_seconds: Optional positive scan deadline in seconds.

    Returns:
        A typed scan result. Expected scan failures, such as an invalid config
        path or non-directory target, are represented as `ScanError` values
        rather than raised exceptions.

    Raises:
        ValueError: If `timeout_seconds` is not positive.
        NativeLibraryError: If the native library cannot load or returns malformed data.
    """
    payload = _scan_payload(
        mode="dir",
        target=os.fspath(path),
        config_path=config_path,
        validation=validation,
        redact=redact,
        timeout_seconds=timeout_seconds,
    )
    return ScanResult.from_native_response(_native_scan_json(payload))


def betterleaks_version() -> str:
    """Return the Betterleaks version bundled into the native bridge."""
    return _native_betterleaks_version()


def _scan_payload(
    *,
    mode: str,
    target: str,
    config_path: Optional[PathInput],
    validation: bool,
    redact: bool,
    timeout_seconds: Optional[float],
) -> dict[str, object]:
    if timeout_seconds is not None and timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")

    return {
        "mode": mode,
        "target": target,
        "config_path": os.fspath(config_path) if config_path is not None else None,
        "validation": validation,
        "redact": redact,
        "timeout_seconds": timeout_seconds,
    }
