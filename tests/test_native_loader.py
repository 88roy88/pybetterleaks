import platform
from pathlib import Path

import pytest
from pybetterleaks import _native
from pybetterleaks.exceptions import NativeLibraryError, NativeLibraryNotFoundError


def test_native_library_name_by_platform() -> None:
    assert _native.native_library_name("Linux") == "libbetterleaks_py.so"
    assert _native.native_library_name("Darwin") == "libbetterleaks_py.dylib"
    assert _native.native_library_name("Windows") == "betterleaks_py.dll"


def test_native_library_name_rejects_unknown_platform() -> None:
    with pytest.raises(NativeLibraryError):
        _native.native_library_name("Plan9")


def test_missing_native_library_error_includes_platform(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    missing = tmp_path / "missing-native-library.so"
    monkeypatch.setenv("PYBETTERLEAKS_NATIVE_LIBRARY", str(missing))
    _native._load_library.cache_clear()

    with pytest.raises(NativeLibraryNotFoundError) as exc_info:
        _native.betterleaks_version()

    message = str(exc_info.value)
    assert str(missing) in message
    assert platform.system() in message

    _native._load_library.cache_clear()
