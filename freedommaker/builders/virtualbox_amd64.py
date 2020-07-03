# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build VirtualBox amd64 images.
"""

from .virtualbox import VirtualBoxImageBuilder


class VirtualBoxAmd64ImageBuilder(VirtualBoxImageBuilder):
    """Image builder for all VirtualBox amd64 targets."""
    architecture = 'amd64'
    kernel_flavor = 'amd64'
