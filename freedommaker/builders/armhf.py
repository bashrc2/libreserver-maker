#
# This file is part of Freedom Maker.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
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
