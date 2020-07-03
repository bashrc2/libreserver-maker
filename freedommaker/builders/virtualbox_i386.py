# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build VirtualBox i386 images.
"""

from .virtualbox import VirtualBoxImageBuilder


class VirtualBoxI386ImageBuilder(VirtualBoxImageBuilder):
    """Image builder for all VirtualBox i386 targets."""
    architecture = 'i386'
    kernel_flavor = '686'
