# SPDX-License-Identifier: GPL-3.0-or-later
"""
Base worker class to build AMD64/Intel images.
"""

from ..builder import ImageBuilder


class AMDIntelImageBuilder(ImageBuilder):
    """Base image build for all Intel/AMD targets."""
    boot_loader = 'grub'

    @classmethod
    def get_target_name(cls):
        """Return the name of the target for an image builder."""
        return getattr(cls, 'architecture', None)
