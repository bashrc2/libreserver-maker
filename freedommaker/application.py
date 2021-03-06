#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Command line application wrapper over image builder.
"""

import argparse
import datetime
import logging
import logging.config
import os

import freedommaker

from .builder import ImageBuilder

IMAGE_SIZE = '7800M'
BUILD_MIRROR = 'http://deb.debian.org/debian'
MIRROR = 'http://deb.debian.org/debian'
DISTRIBUTION = 'bullseye'
BUILD_DIR = 'build'
LOG_LEVEL = 'debug'
HOSTNAME = 'libreserver'

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Application(object):
    """Command line application to build FreedomBox images."""
    def __init__(self):
        """Initialize object."""
        self.arguments = None

    def run(self):
        """Parse the command line args and execute the command."""
        self.parse_arguments()

        self.setup_logging()
        logger.info('Freedom Maker version - %s', freedommaker.__version__)

        try:
            logger.info('Creating directory - %s', self.arguments.build_dir)
            os.makedirs(self.arguments.build_dir)
        except os.error:
            pass

        for target in self.arguments.targets:
            logger.info('Building target - %s', target)

            cls = ImageBuilder.get_builder_class(target)
            if not cls:
                logger.warning('Unknown target - %s', target)
                continue

            builder = cls(self.arguments)
            try:
                builder.build()
                logger.info('Target complete - %s', target)
            except:  # noqa: E722
                logger.error('Target failed - %s', target)
                raise

    def parse_arguments(self):
        """Parse command line arguments."""
        build_stamp = datetime.datetime.today().strftime('%Y-%m-%d')

        parser = argparse.ArgumentParser(
            description='FreedomMaker - Script to build FreedomBox images',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--build-stamp', default=build_stamp,
                            help='Build stamp to use on image file names')
        parser.add_argument('--image-size', default=IMAGE_SIZE,
                            help='Size of the image to build')
        parser.add_argument('--build-mirror', default=BUILD_MIRROR,
                            help='Debian mirror to use for building')
        parser.add_argument('--mirror', default=MIRROR,
                            help='Debian mirror to use in built image')
        parser.add_argument('--distribution', default=DISTRIBUTION,
                            help='Debian release to use in built image')
        parser.add_argument('--add-release-component', action='append',
                            dest='release_component',
                            help='Add an extra Debian release component '
                                 '(other than main)')
        parser.add_argument('--package', action='append',
                            help='Install additional packages in the image')
        parser.add_argument(
            '--custom-package', action='append',
            help='Install package from DEB file into the image')
        parser.add_argument(
            '--enable-backports', action='store_true',
            help='Deprecated: Backports are now enabled for '
            'stable images by default')
        parser.add_argument('--disable-backports', action='store_true',
                            help='Disable backports in the image')
        parser.add_argument(
            '--build-dir', default=BUILD_DIR,
            help='Directory to build images and create log file')
        parser.add_argument(
            '--log-level', default=LOG_LEVEL, help='Log level',
            choices=('critical', 'error', 'warn', 'info', 'debug'))
        parser.add_argument('--hostname', default=HOSTNAME,
                            help='Hostname to set inside the built images')
        parser.add_argument(
            '--sign', action='store_true',
            help='Sign the images with default GPG key after building')
        parser.add_argument(
            '--force', action='store_true',
            help='Force rebuild of images even when required image exists')
        parser.add_argument(
            '--build-in-ram', action='store_true',
            help='Build the image in RAM so that it is faster, requires '
            'free RAM about the size of disk image')
        parser.add_argument('--skip-compression', action='store_true',
                            help='Do not compress the generated image')
        parser.add_argument('--with-build-dep', action='store_true',
                            help='Include build dependencies in the image')
        parser.add_argument('targets', nargs='+',
                            help='Image targets to build')

        self.arguments = parser.parse_args()

    def setup_logging(self):
        """Setup logging."""
        config = {
            'version': 1,
            'formatters': {
                'date': {
                    'format': '%(asctime)s - %(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'date',
                },
            },
            'root': {
                'level': self.arguments.log_level.upper(),
                'handlers': ['console'],
            },
            'disable_existing_loggers': False
        }
        logging.config.dictConfig(config)
