from __future__ import annotations

import asyncio
import contextlib
import functools
import os
import uuid
from collections.abc import Sequence
from typing import Callable, Optional, Union

from ._native import betterleaks_version as _native_betterleaks_version
from ._native import cancel_scan_json as _native_cancel_scan_json
from ._native import scan_json as _native_scan_json
from .config import BetterleaksConfig
from .models import ScanResult

PathInput = Union[str, os.PathLike[str]]


def scan_text(
    text: str,
    *,
    config: Optional[BetterleaksConfig] = None,
    config_path: Optional[PathInput] = None,
    validation: bool = False,
    validation_env_vars: Optional[Sequence[str]] = None,
    redact: bool = True,
    timeout_seconds: Optional[float] = None,
    _request_id: Optional[str] = None,
) -> ScanResult:
    """Scan an in-memory text fragment for secrets.

    Args:
        text: Text content to scan.
        config: Optional typed Betterleaks config. Mutually exclusive with `config_path`.
        config_path: Optional path to a Betterleaks configuration file.
        validation: Enable Betterleaks validation when supported by the rule.
        validation_env_vars: Environment variable names validation Expr may read.
        redact: Replace secret values in findings with `REDACTED`.
        timeout_seconds: Optional positive scan deadline in seconds.

    Returns:
        A typed scan result containing findings, structured native errors, and
        the bundled Betterleaks version.

    Raises:
        ValueError: If `timeout_seconds` is not positive.
        NativeLibraryError: If the native library cannot load or returns malformed data.
    """
    return _scan(
        mode="text",
        target=text,
        git_scope=None,
        config=config,
        config_path=config_path,
        validation=validation,
        validation_env_vars=validation_env_vars,
        redact=redact,
        timeout_seconds=timeout_seconds,
        request_id=_request_id,
    )


def scan_dir(
    path: PathInput,
    *,
    config: Optional[BetterleaksConfig] = None,
    config_path: Optional[PathInput] = None,
    validation: bool = False,
    validation_env_vars: Optional[Sequence[str]] = None,
    redact: bool = True,
    timeout_seconds: Optional[float] = None,
    _request_id: Optional[str] = None,
) -> ScanResult:
    """Scan a directory with the bundled Betterleaks engine.

    Args:
        path: Directory path to scan.
        config: Optional typed Betterleaks config. Mutually exclusive with `config_path`.
        config_path: Optional path to a Betterleaks configuration file.
        validation: Enable Betterleaks validation when supported by the rule.
        validation_env_vars: Environment variable names validation Expr may read.
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
    return _scan(
        mode="dir",
        target=os.fspath(path),
        git_scope=None,
        config=config,
        config_path=config_path,
        validation=validation,
        validation_env_vars=validation_env_vars,
        redact=redact,
        timeout_seconds=timeout_seconds,
        request_id=_request_id,
    )


def scan_git(
    path: PathInput,
    *,
    scope: str = "worktree",
    config: Optional[BetterleaksConfig] = None,
    config_path: Optional[PathInput] = None,
    validation: bool = False,
    validation_env_vars: Optional[Sequence[str]] = None,
    redact: bool = True,
    timeout_seconds: Optional[float] = None,
    _request_id: Optional[str] = None,
) -> ScanResult:
    """Scan a local Git worktree without invoking the Git executable.

    Args:
        path: Repository root or a directory inside a Git worktree.
        scope: Git scan scope. v0.3 initially supports only `"worktree"`.
        config: Optional typed Betterleaks config. Mutually exclusive with `config_path`.
        config_path: Optional path to a Betterleaks configuration file.
        validation: Enable Betterleaks validation when supported by the rule.
        validation_env_vars: Environment variable names validation Expr may read.
        redact: Replace secret values in findings with `REDACTED`.
        timeout_seconds: Optional positive scan deadline in seconds.

    Returns:
        A typed scan result. Invalid repositories are represented as structured
        `ScanError` values rather than raised exceptions.

    Raises:
        ValueError: If `scope` is unsupported or `timeout_seconds` is not positive.
        NativeLibraryError: If the native library cannot load or returns malformed data.
    """
    if scope != "worktree":
        raise ValueError("scan_git currently supports only scope='worktree'")

    return _scan(
        mode="git",
        target=os.fspath(path),
        git_scope=scope,
        config=config,
        config_path=config_path,
        validation=validation,
        validation_env_vars=validation_env_vars,
        redact=redact,
        timeout_seconds=timeout_seconds,
        request_id=_request_id,
    )


async def scan_text_async(
    text: str,
    *,
    config: Optional[BetterleaksConfig] = None,
    config_path: Optional[PathInput] = None,
    validation: bool = False,
    validation_env_vars: Optional[Sequence[str]] = None,
    redact: bool = True,
    timeout_seconds: Optional[float] = None,
) -> ScanResult:
    """Async wrapper for `scan_text` with cooperative native cancellation."""
    request_id = str(uuid.uuid4())
    call = functools.partial(
        scan_text,
        text,
        config=config,
        config_path=config_path,
        validation=validation,
        validation_env_vars=validation_env_vars,
        redact=redact,
        timeout_seconds=timeout_seconds,
        _request_id=request_id,
    )
    return await _run_cancellable(call, request_id)


async def scan_dir_async(
    path: PathInput,
    *,
    config: Optional[BetterleaksConfig] = None,
    config_path: Optional[PathInput] = None,
    validation: bool = False,
    validation_env_vars: Optional[Sequence[str]] = None,
    redact: bool = True,
    timeout_seconds: Optional[float] = None,
) -> ScanResult:
    """Async wrapper for `scan_dir` with cooperative native cancellation."""
    request_id = str(uuid.uuid4())
    call = functools.partial(
        scan_dir,
        path,
        config=config,
        config_path=config_path,
        validation=validation,
        validation_env_vars=validation_env_vars,
        redact=redact,
        timeout_seconds=timeout_seconds,
        _request_id=request_id,
    )
    return await _run_cancellable(call, request_id)


async def scan_git_async(
    path: PathInput,
    *,
    scope: str = "worktree",
    config: Optional[BetterleaksConfig] = None,
    config_path: Optional[PathInput] = None,
    validation: bool = False,
    validation_env_vars: Optional[Sequence[str]] = None,
    redact: bool = True,
    timeout_seconds: Optional[float] = None,
) -> ScanResult:
    """Async wrapper for `scan_git` with cooperative native cancellation."""
    request_id = str(uuid.uuid4())
    call = functools.partial(
        scan_git,
        path,
        scope=scope,
        config=config,
        config_path=config_path,
        validation=validation,
        validation_env_vars=validation_env_vars,
        redact=redact,
        timeout_seconds=timeout_seconds,
        _request_id=request_id,
    )
    return await _run_cancellable(call, request_id)


def betterleaks_version() -> str:
    """Return the Betterleaks version bundled into the native bridge."""
    return _native_betterleaks_version()


def _scan(
    *,
    mode: str,
    target: str,
    git_scope: Optional[str],
    config: Optional[BetterleaksConfig],
    config_path: Optional[PathInput],
    validation: bool,
    validation_env_vars: Optional[Sequence[str]],
    redact: bool,
    timeout_seconds: Optional[float],
    request_id: Optional[str],
) -> ScanResult:
    if config is not None and config_path is not None:
        raise ValueError("config and config_path are mutually exclusive")

    payload = _scan_payload(
        mode=mode,
        target=target,
        git_scope=git_scope,
        request_id=request_id,
        config_path=config_path,
        config_toml=config.to_toml() if config is not None else None,
        validation=validation,
        validation_env_vars=validation_env_vars,
        redact=redact,
        timeout_seconds=timeout_seconds,
    )
    return ScanResult.from_native_response(_native_scan_json(payload))


def _scan_payload(
    *,
    mode: str,
    target: str,
    git_scope: Optional[str],
    request_id: Optional[str],
    config_path: Optional[PathInput],
    config_toml: Optional[str],
    validation: bool,
    validation_env_vars: Optional[Sequence[str]],
    redact: bool,
    timeout_seconds: Optional[float],
) -> dict[str, object]:
    if timeout_seconds is not None and timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")

    return {
        "mode": mode,
        "target": target,
        "git_scope": git_scope,
        "request_id": request_id,
        "config_path": os.fspath(config_path) if config_path is not None else None,
        "config_toml": config_toml,
        "validation": validation,
        "validation_env_vars": list(validation_env_vars or []),
        "validation_env": {
            name: os.environ[name] for name in validation_env_vars or [] if name in os.environ
        },
        "redact": redact,
        "timeout_seconds": timeout_seconds,
    }


async def _run_cancellable(
    call: Callable[[], ScanResult],
    request_id: str,
) -> ScanResult:
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(None, call)
    try:
        return await future
    except asyncio.CancelledError:
        with contextlib.suppress(Exception):
            _native_cancel_scan_json(request_id)
        raise
