# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build AMD64 images.
"""

from .amd_intel import AMDIntelImageBuilder


class AMD64ImageBuilder(AMDIntelImageBuilder):
    """Image builder for all amd64 targets."""
    architecture = 'amd64'
    kernel_flavor = 'amd64'
