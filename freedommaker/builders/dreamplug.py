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
Worker class to build GlobalScale Dreamplug image.
"""

import logging

from .. import library
from .arm import ARMImageBuilder

logger = logging.getLogger(__name__)


class DreamPlugImageBuilder(ARMImageBuilder):
    """Image builder for DreamPlug target."""
    architecture = 'armel'
    machine = 'dreamplug'
    kernel_flavor = 'marvell'
    boot_filesystem_type = 'vfat'
    flash_kernel_name = 'Globalscale Technologies Dreamplug'

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        # flash-kernel's hook-functions provided to mkinitramfs have the
        # unfortunate side-effect of creating /conf/param.conf in the initrd
        # when run from our emulated chroot environment, which means our root=
        # on the kernel command line is completely ignored!  repack the initrd
        # to remove this evil...
        script = r'''
set -e
set -x
set -o pipefail

kernelVersion=$(ls /usr/lib/*/kirkwood-dreamplug.dtb | head -1 | cut -d/ -f4)
version=$(echo $kernelVersion | sed 's/linux-image-\(.*\)/\1/')
initRd=initrd.img-$version
vmlinuz=vmlinuz-$version

mkdir /tmp/initrd-repack

(cd /tmp/initrd-repack ; \
    zcat /boot/$initRd | cpio -i ; \
    rm -f conf/param.conf ; \
    find . | cpio --quiet -o -H newc | \
    gzip -9 > /boot/$initRd )

rm -rf /tmp/initrd-repack

(cd /boot ; \
    cp /usr/lib/$kernelVersion/kirkwood-dreamplug.dtb dtb ; \
    cat $vmlinuz dtb >> temp-kernel ; \
    mkimage -A arm -O linux -T kernel -n "Debian kernel ${version}" \
    -C none -a 0x8000 -e 0x8000 -d temp-kernel uImage ; \
    rm -f temp-kernel ; \
    mkimage -A arm -O linux -T ramdisk -C gzip -a 0x0 -e 0x0 \
    -n "Debian ramdisk ${version}" \
    -d $initRd uInitrd )
'''
        library.run_in_chroot(state, ['bash', '-c', script])

        logger.info('Adding a getty on the serial port')
        script = r'''
echo "T0:12345:respawn:/sbin/getty -L ttyS0 115200 vt100" >> /etc/inittab
'''
        library.run_in_chroot(state, ['bash', '-c', script])
