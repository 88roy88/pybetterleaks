from __future__ import annotations

from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel


class platform_bdist_wheel(bdist_wheel):
    """Force platform wheel tags for wheels carrying bundled native libraries."""

    def finalize_options(self) -> None:
        super().finalize_options()
        self.root_is_pure = False


setup(cmdclass={"bdist_wheel": platform_bdist_wheel})
