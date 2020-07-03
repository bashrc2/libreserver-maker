# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build i386 images.
"""

from .amd_intel import AMDIntelImageBuilder


class I386ImageBuilder(AMDIntelImageBuilder):
    """Image builder for all i386 targets."""
    architecture = 'i386'
    kernel_flavor = '686'
