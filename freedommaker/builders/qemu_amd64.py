# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build Qemu AMD64 images.
"""

from .qemu import QemuImageBuilder


class QemuAmd64ImageBuilder(QemuImageBuilder):
    """Image builder for all Qemu amd64 targets."""
    architecture = 'amd64'
    kernel_flavor = 'amd64'
