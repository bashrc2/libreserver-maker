# SPDX-License-Identifier: GPL-3.0-or-later
"""
Base worker class to build all ARM images.
"""

from ..builder import ImageBuilder


class ARMImageBuilder(ImageBuilder):
    """Base image builder for all ARM targets."""
    boot_loader = 'u-boot'
    boot_filesystem_type = 'ext2'
    boot_size = '128MiB'

    @classmethod
    def get_target_name(cls):
        """Return the name of the target for an image builder."""
        return getattr(cls, 'machine', None)
