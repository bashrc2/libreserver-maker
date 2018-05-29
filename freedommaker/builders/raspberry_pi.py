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
Worker class to build Raspberry Pi image.
"""

from .. import library
from .arm import ARMImageBuilder


class RaspberryPiImageBuilder(ARMImageBuilder):
    """Image builder for Raspberry Pi target."""
    architecture = 'armel'
    machine = 'raspberry'
    free = False
    boot_loader = None
    root_filesystem_type = 'ext4'
    boot_filesystem_type = 'vfat'
    kernel_flavor = None

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        script = '''
set -e
set -x
set -o pipefail

apt-get install -y git-core binutils ca-certificates wget kmod

# Raspberry Pi blob repo
rpi_blob_repo='https://github.com/Hexxeh/rpi-update'
rpi_blob_commit='31615deb9406ffc3ab823e76d12dedf373c8e087'

# Expected sha256 hash for rpi-update
rpi_blob_hash='9868671978541ae6efa692d087028ee5cc5019c340296fdd17793160b6cf403f'

rpi_tempdir=/tmp/fbx-rpi-update
if [ -d $rpi_tempdir ]; then
    rm -rf $rpi_tempdir
fi
git clone $rpi_blob_repo $rpi_tempdir
cd $rpi_tempdir
git checkout $rpi_blob_commit -b $rpi_blob_commit

downloaded_rpi_blob_hash=$(sha256sum $rpi_tempdir/rpi-update | awk -F ' ' '{print $1}')
if [ "$downloaded_rpi_blob_hash" != "$rpi_blob_hash" ]; then
    echo 'WARNING: Unable to verify Raspberry Pi boot blob'
    return
fi

cp $rpi_tempdir/rpi-update /usr/bin/rpi-update

chmod a+x /usr/bin/rpi-update
mkdir -p /lib/modules
touch /boot/start.elf
SKIP_BACKUP=1 SKIP_WARNING=1 rpi-update | tee /root/rpi-update.log
'''
        library.run_in_chroot(state, ['bash', '-c', script])
