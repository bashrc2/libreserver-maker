#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Tool to build FreedomBox images for various targets.
"""

from .application import Application

__version__ = '0.28'

__all__ = [
    'Application',
    'main',
]


def main():
    Application().run()
