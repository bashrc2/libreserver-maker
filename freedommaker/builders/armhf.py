# SPDX-License-Identifier: GPL-3.0-or-later
"""
Worker class to build a universal ARM32 images using UEFI.
"""

from .arm_efi import ARMEFIImageBuilder


class ARMHFImageBuilder(ARMEFIImageBuilder):
    """Image builder a universal ARM32 images using UEFI."""
    architecture = 'armhf'
    kernel_flavor = 'armmp-lpae'
    efi_architecture = 'arm'
    grub_target = 'arm-efi'

    def __init__(self, *args, **kwargs):
        """Initialize builder object."""
        super().__init__(*args, **kwargs)
        self.packages += ['grub-efi-arm']

    @classmethod
    def get_target_name(cls):
        """Return the command line name of target for this builder."""
        return 'armhf'
