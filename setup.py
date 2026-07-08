from __future__ import annotations

from setuptools import Distribution, setup


class BinaryDistribution(Distribution):
    """Mark wheels as platform-specific because they include a native library."""

    def has_ext_modules(self) -> bool:
        return True


setup(distclass=BinaryDistribution)
