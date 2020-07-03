#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Module to provide ability to run this freedommaker package.

Run the package as:
  python3 -m freedommaker
"""

from .application import Application

if __name__ == '__main__':
    Application().run()
