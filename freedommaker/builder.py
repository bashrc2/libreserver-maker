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
Base worker class to run various commands that build the image.
"""

import logging
import os

from . import internal, library

# initramfs-tools is a dependency for the kernel-image package. However, when
# kernel is not installed, as in case of Raspberry Pi image, explicit dependency
# is needed.
BASE_PACKAGES = [
    'initramfs-tools',
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

    extra_storage_size = '1000M'

    @classmethod
    def get_target_name(cls):
        """Return the command line name of target for this builder."""
        return None

    @classmethod
    def get_builder_class(cls, target):
        """Return an builder class given target name."""
        from . import builders  # pylint: disable=unused-variable

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
        self.ram_directory = None

        self.builder_backends = {}
        self.builder_backends['internal'] = internal.InternalBuilderBackend(
            self)

        self.image_file = os.path.join(self.arguments.build_dir,
                                       self._get_image_base_name() + '.img')

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

    def compress(self, archive_file, image_file):
        """Compress the generate image."""
        if not self.arguments.skip_compression:
            library.compress(archive_file, image_file)
        else:
            logger.info('Skipping image compression')

    def sign(self, archive):
        """Signed the final output image."""
        if not self.arguments.sign:
            return

        library.sign(archive)

    @staticmethod
    def _replace_extension(file_name, new_extension):
        """Replace a file's extension with a new extention."""
        return file_name.rsplit('.', maxsplit=1)[0] + new_extension
