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
Worker class to build a universal ARM64/ARM32 images using UEFI.
"""

import pathlib

from .. import library
from ..builder import ImageBuilder

DTB_SCRIPT = '''#!/bin/sh

set -e

if [ ! -e /boot/efi/ ]; then
    exit 0
fi

# See Chapter 8 of Debian Linux Kernel Handbook
set -- $DEB_MAINT_PARAMS
action="$1"
action="${action#\'}"
action="${action%\'}"

# Only call once on install, upgrade, removal or purge
hook="$(basename "$(dirname "$0")")"
case "$hook:$action" in
  postinst.d:configure|postinst.d:|postrm.d:remove|postrm.d:)
    latest_version=$(linux-version list | linux-version sort | tail -1)
    source_dir="/usr/lib/linux-image-${latest_version}"
    if [ -d "${source_dir}" ]; then
      echo "Copying DTBs from ${source_dir} to EFI partition" >&2
      rm -rf /boot/efi/dtb
      cp -r "${source_dir}" /boot/efi/dtb
    fi
  ;;
esac
'''


class ARMEFIImageBuilder(ImageBuilder):
    """Image builder a universal ARM64/ARM32 images using UEFI."""
    efi_architecture = None
    partition_table_type = 'gpt'
    efi_filesystem_type = 'vfat'
    efi_size = '256mib'
    boot_loader = None
    grub_target = None

    def __init__(self, *args, **kwargs):
        """Initialize the object."""
        super().__init__(*args, **kwargs)
        if not self.efi_architecture:
            raise Exception('EFI architecture is not specified')

    @classmethod
    def install_boot_loader(cls, state):
        """Install the DTB files and boot manager."""
        library.install_grub(state, target=cls.grub_target)

        # In typical UEFI systems, EFI boot manager is available and all the OS
        # list themselves as boot manager configuration in NVRAM. In many SBCs,
        # NVRAM may not be present. In our case, since we distribute disk
        # images, we don't have other operating system to boot. So, install
        # grub as the boot manager.
        library.run_in_chroot(state, ['mkdir', '-p', '/boot/efi/EFI/boot/'])
        library.run_in_chroot(state, [
            'cp', f'/boot/efi/EFI/debian/grub{cls.efi_architecture}.efi',
            f'/boot/efi/EFI/boot/boot{cls.efi_architecture}.efi'
        ])

        # Grub does not have a way of providing the kernel with an appropriate
        # DTB file need to understand the hardware layout of an SBC. u-boot
        # firmware provided by the SBC manufacturer can perform this task if
        # the DTB suitable for the board is available in /dtb/ directory of the
        # EFI partition.
        usr_lib = pathlib.Path(library.path_in_mount(state, 'usr/lib/'))
        linux = list(usr_lib.glob('linux-image-*'))[0].name
        library.run_in_chroot(
            state, ['cp', '-r', f'/usr/lib/{linux}/', '/boot/efi/dtb'])

        # Install a permanent script that would continuously update DTBs after
        # newer kernels are installed.
        dir1 = library.path_in_mount(state, 'etc/kernel/postinst.d/')
        dir2 = library.path_in_mount(state, 'etc/kernel/postrm.d/')
        for directory in [dir1, dir2]:
            script = pathlib.Path(directory) / 'zz-freedombox-efi-dtbs'
            script.write_text(DTB_SCRIPT)
            script.chmod(0o755)
