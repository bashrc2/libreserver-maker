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
Worker class to run various command build the image.
"""

import logging
import os
import tempfile

from . import internal
from . import library

BASE_PACKAGES = [
    'initramfs-tools',
]

NEXT_RELEASE_PACKAGES = [
    'firmware-ath9k-htc',
]

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ImageBuilder(object):  # pylint: disable=too-many-instance-attributes
    """Base for all image builders."""
    architecture = None
    machine = 'all'
    free = True

    builder_backend = 'internal'
    root_filesystem_type = 'btrfs'
    boot_filesystem_type = None
    boot_size = None
    boot_offset = None
    firmware_filesystem_type = None
    firmware_size = None
    kernel_flavor = 'default'
    debootstrap_variant = None

    @classmethod
    def get_target_name(cls):
        """Return the command line name of target for this builder."""
        return None

    @classmethod
    def get_builder_class(cls, target):
        """Return an builder class given target name."""
        for subclass in cls.get_subclasses():
            if subclass.get_target_name() == target:
                return subclass

        raise ValueError('No such target')

    @classmethod
    def get_subclasses(cls):
        """Iterate through the subclasses of this class."""
        for subclass in cls.__subclasses__():
            yield subclass
            yield from subclass.get_subclasses()

    def __init__(self, arguments):
        """Initialize object."""
        self.arguments = arguments
        self.packages = BASE_PACKAGES
        if self.arguments.distribution in [
                'unstable', 'testing', 'sid', 'buster'
        ]:
            self.packages += NEXT_RELEASE_PACKAGES

        self.ram_directory = None

        self.builder_backends = {}
        self.builder_backends['internal'] = internal.InternalBuilderBackend(
            self)

        self.image_file = os.path.join(self.arguments.build_dir,
                                       self._get_image_base_name() + '.img')

    def cleanup(self):
        """Finalize tasks."""
        logger.info('Cleaning up')
        if self.ram_directory:
            library.run(['sudo', 'umount', self.ram_directory.name])
            self.ram_directory.cleanup()
            self.ram_directory = None

    def build(self):
        """Run the image building process."""
        archive_file = self.image_file + '.xz'
        self.make_image()
        self.compress(archive_file, self.image_file)

        self.sign(archive_file)

    def make_image(self):
        """Call a builder backend to create basic image."""
        builder = self.builder_backend
        self.builder_backends[builder].make_image()

    def _get_image_base_name(self):
        """Return the base file name of the final image."""
        free_tag = 'free' if self.free else 'nonfree'

        return 'freedombox-{distribution}-{free_tag}_{build_stamp}_{machine}' \
            '-{architecture}'.format(
                distribution=self.arguments.distribution, free_tag=free_tag,
                build_stamp=self.arguments.build_stamp, machine=self.machine,
                architecture=self.architecture)

    def get_temp_image_file(self):
        """Get the temporary path to where the image should be built.

        If building to RAM is enabled, create a temporary directory, mount
        tmpfs in it and return a path in that directory. This is so that builds
        that happen in RAM will be faster.

        If building to RAM is disabled, append .temp to the final file name and
        return it.

        """
        if not self.arguments.build_in_ram:
            return self.image_file + '.temp'

        self.ram_directory = tempfile.TemporaryDirectory()
        library.run([
            'sudo', 'mount', '-o', 'size=' + self.arguments.image_size, '-t',
            'tmpfs', 'tmpfs', self.ram_directory.name
        ])
        return os.path.join(self.ram_directory.name,
                            os.path.basename(self.image_file))

    @staticmethod
    def compress(archive_file, image_file):
        """Compress the generate image."""
        library.compress(archive_file, image_file)

    def sign(self, archive):
        """Signed the final output image."""
        if not self.arguments.sign:
            return

        library.sign(archive)

    @staticmethod
    def _replace_extension(file_name, new_extension):
        """Replace a file's extension with a new extention."""
        return file_name.rsplit('.', maxsplit=1)[0] + new_extension


class AMDIntelImageBuilder(ImageBuilder):
    """Base image build for all Intel/AMD targets."""
    boot_loader = 'grub'

    @classmethod
    def get_target_name(cls):
        """Return the name of the target for an image builder."""
        return getattr(cls, 'architecture', None)


class AMD64ImageBuilder(AMDIntelImageBuilder):
    """Image builder for all amd64 targets."""
    architecture = 'amd64'
    kernel_flavor = 'amd64'


class I386ImageBuilder(AMDIntelImageBuilder):
    """Image builder for all i386 targets."""
    architecture = 'i386'
    kernel_flavor = '686'


class VMImageBuilder(AMDIntelImageBuilder):
    """Base image builder for all virtual machine targets."""
    vm_image_extension = None

    def build(self):
        """Run the image building process."""
        vm_file = self._replace_extension(self.image_file,
                                          self.vm_image_extension)
        vm_archive_file = vm_file + '.xz'

        self.make_image()
        self.create_vm_file(self.image_file, vm_file)
        os.remove(self.image_file)
        self.compress(vm_archive_file, vm_file)

        self.sign(vm_archive_file)

    def create_vm_file(self, image_file, vm_file):
        """Create a VM image from image file."""
        raise Exception('Not reached')


class VirtualBoxImageBuilder(VMImageBuilder):
    """Base image builder for all VirutalBox targets."""
    vm_image_extension = '.vdi'

    @classmethod
    def get_target_name(cls):
        """Return the name of the target for an image builder."""
        if getattr(cls, 'architecture', None):
            return 'virtualbox-' + cls.architecture

        return None

    def create_vm_file(self, image_file, vm_file):
        """Create a VM file from image file."""
        try:
            os.remove(vm_file)
        except FileNotFoundError:
            pass

        library.run(['VBoxManage', 'convertdd', image_file, vm_file])


class VirtualBoxAmd64ImageBuilder(VirtualBoxImageBuilder):
    """Image builder for all VirutalBox amd64 targets."""
    architecture = 'amd64'
    kernel_flavor = 'amd64'


class VirtualBoxI386ImageBuilder(VirtualBoxImageBuilder):
    """Image builder for all VirutalBox i386 targets."""
    architecture = 'i386'
    kernel_flavor = '686'


class VagrantImageBuilder(VirtualBoxAmd64ImageBuilder):
    """Image builder for Vagrant package."""
    vagrant_extension = '.box'

    @classmethod
    def get_target_name(cls):
        """Return the name of the target for an image builder."""
        return 'vagrant'

    def build(self):
        """Run the image building process."""
        vm_file = self._replace_extension(self.image_file,
                                          self.vm_image_extension)
        vagrant_file = self._replace_extension(self.image_file,
                                               self.vagrant_extension)

        self.make_image()
        self.create_vm_file(self.image_file, vm_file)
        os.remove(self.image_file)
        self.vagrant_package(vm_file, vagrant_file)

    @staticmethod
    def vagrant_package(vm_file, vagrant_file):
        """Create a vagrant package from VM file."""
        library.run(
            ['sudo', 'bin/vagrant-package', '--output', vagrant_file, vm_file])


class QemuImageBuilder(VMImageBuilder):
    """Base image builder for all Qemu targets."""
    vm_image_extension = '.qcow2'

    @classmethod
    def get_target_name(cls):
        """Return the name of the target for an image builder."""
        if getattr(cls, 'architecture', None):
            return 'qemu-' + cls.architecture

        return None

    def create_vm_file(self, image_file, vm_file):
        """Create a VM image file from image file."""
        library.run(['qemu-img', 'convert', '-O', 'qcow2', image_file, vm_file])


class QemuAmd64ImageBuilder(QemuImageBuilder):
    """Image builder for all Qemu amd64 targets."""
    architecture = 'amd64'
    kernel_flavor = 'amd64'


class QemuI386ImageBuilder(QemuImageBuilder):
    """Image builder for all Qemu i386 targets."""
    architecture = 'i386'
    kernel_flavor = '686'


class ARMImageBuilder(ImageBuilder):
    """Base image builder for all ARM targets."""
    boot_loader = 'u-boot'
    boot_filesystem_type = 'ext2'
    boot_size = '128mib'

    @classmethod
    def get_target_name(cls):
        """Return the name of the target for an image builder."""
        return getattr(cls, 'machine', None)


class BeagleBoneImageBuilder(ARMImageBuilder):
    """Image builder for BeagleBone target."""
    architecture = 'armhf'
    machine = 'beaglebone'
    kernel_flavor = 'armmp'
    boot_offset = '2mib'
    flash_kernel_name = 'TI AM335x BeagleBone Black'
    flash_kernel_options = 'console=ttyO0'

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        library.install_boot_loader_part(
            state,
            'usr/lib/u-boot/am335x_boneblack/MLO',
            seek='1',
            size='128k',
            count='1')
        library.install_boot_loader_part(
            state,
            'usr/lib/u-boot/am335x_boneblack/u-boot.img',
            seek='1',
            size='384k',
            count='2')


class A20ImageBuilder(ARMImageBuilder):
    """Base image builder for all Allwinner A20 board based targets."""
    architecture = 'armhf'
    kernel_flavor = 'armmp-lpae'
    boot_offset = '1mib'


class A20OLinuXinoLimeImageBuilder(A20ImageBuilder):
    """Image builder for A20 OLinuXino Lime targets."""
    machine = 'a20-olinuxino-lime'
    flash_kernel_name = 'Olimex A20-OLinuXino-LIME'

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        library.install_boot_loader_part(
            state,
            'usr/lib/u-boot/A20-OLinuXino-Lime/u-boot-sunxi-with-spl.bin',
            seek='8',
            size='1k')


class A20OLinuXinoLime2ImageBuilder(A20ImageBuilder):
    """Image builder for A20 OLinuXino Lime2 targets."""
    machine = 'a20-olinuxino-lime2'
    flash_kernel_name = 'Olimex A20-OLinuXino-LIME2'

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        library.install_boot_loader_part(
            state,
            'usr/lib/u-boot/A20-OLinuXino-Lime2/u-boot-sunxi-with-spl.bin',
            seek='8',
            size='1k')


class A20OLinuXinoMicroImageBuilder(A20ImageBuilder):
    """Image builder for A20 OLinuXino Micro targets."""
    machine = 'a20-olinuxino-micro'
    flash_kernel_name = 'Olimex A20-Olinuxino Micro'

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        library.install_boot_loader_part(
            state,
            'usr/lib/u-boot/A20-OLinuXino_MICRO/u-boot-sunxi-with-spl.bin',
            seek='8',
            size='1k')


class BananaProImageBuilder(A20ImageBuilder):
    """Image builder for Banana Pro target."""
    machine = 'banana-pro'
    flash_kernel_name = 'LeMaker Banana Pro'

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        library.install_boot_loader_part(
            state,
            'usr/lib/u-boot/Bananapro/u-boot-sunxi-with-spl.bin',
            seek='8',
            size='1k')


class Cubieboard2ImageBuilder(A20ImageBuilder):
    """Image builder for Cubieboard 2 target."""
    machine = 'cubieboard2'
    flash_kernel_name = 'Cubietech Cubieboard2'

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        library.install_boot_loader_part(
            state,
            'usr/lib/u-boot/Cubieboard2/u-boot-sunxi-with-spl.bin',
            seek='8',
            size='1k')


class CubietruckImageBuilder(A20ImageBuilder):
    """Image builder for Cubietruck (Cubieboard 3) target."""
    machine = 'cubietruck'
    flash_kernel_name = 'Cubietech Cubietruck'

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        library.install_boot_loader_part(
            state,
            'usr/lib/u-boot/Cubietruck/u-boot-sunxi-with-spl.bin',
            seek='8',
            size='1k')


class PCDuino3ImageBuilder(A20ImageBuilder):
    """Image builder for PCDuino3 target."""
    machine = 'pcduino3'
    flash_kernel_name = 'LinkSprite pcDuino3'

    @staticmethod
    def install_boot_loader(state):
        """Install the boot loader onto the image."""
        library.install_boot_loader_part(
            state,
            'usr/lib/u-boot/Linksprite_pcDuino3/u-boot-sunxi-with-spl.bin',
            seek='8',
            size='1k')


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


class RaspberryPiWithUBoot(ARMImageBuilder):
    """Base image builder for Raspberry Pi 2 and 3 targets."""
    free = False
    uboot_variant = None
    firmware_filesystem_type = 'vfat'
    firmware_size = '60mib'

    def install_boot_loader(self, state):
        """Install the boot loader onto the image."""
        if not self.uboot_variant:
            raise NotImplementedError

        script = '''
set -e
set -x
set -o pipefail

apt-get install --no-install-recommends -y dpkg-dev
cd /tmp
apt-get source raspi3-firmware
cp raspi3-firmware*/boot/* /boot/firmware
rm -rf raspi3-firmware*
cd /

# remove unneeded firmware files
rm -f /boot/firmware/fixup_*
rm -f /boot/firmware/start_*

# u-boot setup
apt-get install -y u-boot-rpi
cp /usr/lib/u-boot/{uboot_variant}/u-boot.bin /boot/firmware/kernel.img
'''.format(uboot_variant=self.uboot_variant)
        library.run_in_chroot(state, ['bash', '-c', script])


class RaspberryPi2ImageBuilder(RaspberryPiWithUBoot):
    """Image builder for Raspberry Pi 2 target."""
    architecture = 'armhf'
    machine = 'raspberry2'
    boot_offset = '64mib'
    kernel_flavor = 'armmp'
    flash_kernel_name = 'Raspberry Pi 2 Model B'
    uboot_variant = 'rpi_2'


class RaspberryPi3ImageBuilder(RaspberryPiWithUBoot):
    """Image builder for Raspberry Pi 3 target."""
    architecture = 'armhf'
    machine = 'raspberry3'
    free = False
    boot_offset = '64mib'
    kernel_flavor = 'armmp'
    flash_kernel_name = 'Raspberry Pi 3 Model B'
    uboot_variant = 'rpi_3_32b'
