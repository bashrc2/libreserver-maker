# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build a universal ARM64 images using UEFI.
"""

from .arm_efi import ARMEFIImageBuilder


class ARM64ImageBuilder(ARMEFIImageBuilder):
    """Image builder a universal ARM64 images using UEFI."""
    architecture = 'arm64'
    kernel_flavor = 'arm64'
    efi_architecture = 'aa64'

    def __init__(self, *args, **kwargs):
        """Initialize builder object."""
        super().__init__(*args, **kwargs)
        self.packages += ['grub-efi-arm64']

    @classmethod
    def get_target_name(cls):
        """Return the command line name of target for this builder."""
        return 'arm64'
