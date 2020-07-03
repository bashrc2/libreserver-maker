# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Qemu i386 images.
"""

from .qemu import QemuImageBuilder


class QemuI386ImageBuilder(QemuImageBuilder):
    """Image builder for all Qemu i386 targets."""
    architecture = 'i386'
    kernel_flavor = '686'
