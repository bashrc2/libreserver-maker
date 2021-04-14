#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Freedom Maker setup file
"""

import setuptools

from freedommaker import __version__

setuptools.setup(
    name='freedom-maker',
    version=__version__,
    description='The LibreServer image builder',
    author='FreedomBox Authors',
    author_email='bob@libreserver.org',
    url='https://libreserver.org',
    packages=setuptools.find_packages(),
    scripts=['bin/passwd-in-image', 'bin/vagrant-package'],
    entry_points={'console_scripts': ['freedom-maker = freedommaker:main']},
    test_suite='freedommaker.tests',
    license='COPYING',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: DFSG approved',
        'License :: OSI Approved :: '
        'GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Unix Shell',
        'Topic :: System :: Software Distribution',
    ],
    include_package_data=True,
)
