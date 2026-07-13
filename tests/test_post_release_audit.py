from __future__ import annotations

import pytest

from scripts import post_release_audit

SHA_1 = "1" * 64
SHA_2 = "2" * 64


def test_validate_pypi_release_accepts_wheels_with_digests() -> None:
    release_files = post_release_audit.validate_pypi_release(
        {
            "releases": {
                "0.6.0": [
                    {
                        "filename": "pybetterleaks-0.6.0-py3-none-manylinux_2_28_x86_64.whl",
                        "packagetype": "bdist_wheel",
                        "digests": {"sha256": SHA_1},
                    }
                ]
            }
        },
        version="0.6.0",
    )

    assert release_files == [
        post_release_audit.ReleaseFile(
            filename="pybetterleaks-0.6.0-py3-none-manylinux_2_28_x86_64.whl",
            sha256=SHA_1,
            packagetype="bdist_wheel",
        )
    ]


def test_validate_pypi_release_rejects_musllinux_wheels() -> None:
    with pytest.raises(ValueError, match="musllinux artifact"):
        post_release_audit.validate_pypi_release(
            {
                "releases": {
                    "0.6.0": [
                        {
                            "filename": (
                                "pybetterleaks-0.6.0-py3-none-musllinux_1_2_x86_64.whl"
                            ),
                            "packagetype": "bdist_wheel",
                            "digests": {"sha256": SHA_1},
                        }
                    ]
                }
            },
            version="0.6.0",
        )


def test_parse_checksums_rejects_paths() -> None:
    with pytest.raises(ValueError, match="must not contain paths"):
        post_release_audit.parse_checksums(f"{SHA_1}  dist/artifact.whl\n")


def test_validate_checksums_accepts_exact_pypi_file_set() -> None:
    release_files = [
        post_release_audit.ReleaseFile(
            filename="pybetterleaks-0.6.0-py3-none-manylinux_2_28_x86_64.whl",
            sha256=SHA_1,
            packagetype="bdist_wheel",
        ),
        post_release_audit.ReleaseFile(
            filename="pybetterleaks-0.6.0-py3-none-macosx_11_0_arm64.whl",
            sha256=SHA_2,
            packagetype="bdist_wheel",
        ),
    ]

    entries = post_release_audit.parse_checksums(
        "\n".join(
            [
                f"{SHA_1}  pybetterleaks-0.6.0-py3-none-manylinux_2_28_x86_64.whl",
                f"{SHA_2}  pybetterleaks-0.6.0-py3-none-macosx_11_0_arm64.whl",
            ]
        )
    )

    post_release_audit.validate_checksums(release_files, entries)


def test_validate_checksums_rejects_missing_extra_and_mismatch() -> None:
    release_files = [
        post_release_audit.ReleaseFile(
            filename="artifact.whl",
            sha256=SHA_1,
            packagetype="bdist_wheel",
        )
    ]

    with pytest.raises(ValueError, match="missing PyPI"):
        post_release_audit.validate_checksums(release_files, {})

    with pytest.raises(ValueError, match="non-PyPI"):
        post_release_audit.validate_checksums(
            release_files,
            {"artifact.whl": SHA_1, "extra.whl": SHA_2},
        )

    with pytest.raises(ValueError, match="digest mismatch"):
        post_release_audit.validate_checksums(release_files, {"artifact.whl": SHA_2})


def test_find_asset_returns_named_asset() -> None:
    asset = post_release_audit.find_asset(
        {
            "assets": [
                {
                    "name": "SHA256SUMS",
                    "browser_download_url": "https://example.test/SHA256SUMS",
                }
            ]
        },
        "SHA256SUMS",
    )

    assert asset.name == "SHA256SUMS"
    assert asset.download_url == "https://example.test/SHA256SUMS"
