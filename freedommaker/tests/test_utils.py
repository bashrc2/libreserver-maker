# SPDX-License-Identifier: GPL-3.0-or-later
"""
Tests for miscellaneous utility methods.
"""

import unittest

from freedommaker import utils


class TestUtils(unittest.TestCase):
    """Test for miscellaneous utility methods."""
    def test_add_disk_offsets(self):
        """Test disk offset addition."""
        self.assertEqual(utils.add_disk_offsets('1MiB', '2MiB'), '3MiB')
        # mib is not allowed as unit. Only MiB.        
        self.assertRaises(NotImplementedError, utils.add_disk_offsets, '1mib',
                         '1mib')
        self.assertRaises(NotImplementedError, utils.add_disk_offsets, '1GiB',
                          '1MiB')
        self.assertRaises(NotImplementedError, utils.add_disk_offsets, '1MiB',
                          '1GiB')
        self.assertRaises(ValueError, utils.add_disk_offsets, 'xMiB', '1MiB')
        self.assertRaises(ValueError, utils.add_disk_offsets, 'xMiB', 'xMiB')

    def test_parse_disk_size(self):
        """Test parsing disk sizes."""
        self.assertEqual(utils.parse_disk_size(0), 0)
        self.assertEqual(utils.parse_disk_size(123), 123)
        self.assertEqual(utils.parse_disk_size('123'), 123)
        self.assertEqual(utils.parse_disk_size('123b'), 123)
        self.assertEqual(utils.parse_disk_size('123k'), 123 * 1024)
        self.assertEqual(utils.parse_disk_size('123K'), 123 * 1024)
        self.assertEqual(utils.parse_disk_size('123M'), 123 * 1024 * 1024)
        self.assertEqual(utils.parse_disk_size('123G'),
                         123 * 1024 * 1024 * 1024)
        self.assertEqual(utils.parse_disk_size('123T'),
                         123 * 1024 * 1024 * 1024 * 1024)
        self.assertRaises(ValueError, utils.parse_disk_size, '-1M')
        self.assertRaises(ValueError, utils.parse_disk_size, '1B')
        self.assertRaises(ValueError, utils.parse_disk_size, '1P')
        self.assertRaises(ValueError, utils.parse_disk_size, 'test')

    def test_format_disk_size(self):
        """Test that formatting disk sizes works."""
        self.assertEqual(utils.format_disk_size(0), '0')
        self.assertEqual(utils.format_disk_size(1), '1')
        self.assertEqual(utils.format_disk_size(1023), '1023')
        self.assertEqual(utils.format_disk_size(1024), '1K')
        self.assertEqual(utils.format_disk_size(1023 * 1023), '1046529')
        self.assertEqual(utils.format_disk_size(1023 * 1024), '1023K')
        self.assertEqual(utils.format_disk_size(1024 * 1024), '1M')
        self.assertEqual(utils.format_disk_size(1023 * 1024 * 1024), '1023M')
        self.assertEqual(utils.format_disk_size(1024 * 1024 * 1024), '1G')
        self.assertEqual(utils.format_disk_size(1023 * 1024 * 1024 * 1024),
                         '1023G')
        self.assertEqual(utils.format_disk_size(1024 * 1024 * 1024 * 1024),
                         '1T')
        self.assertEqual(
            utils.format_disk_size(1023 * 1024 * 1024 * 1024 * 1024), '1023T')

    def test_add_disk_sizes(self):
        """Test that adding two disk sizes works as expected."""
        self.assertEqual(utils.add_disk_sizes('1M', '1K'), '1025K')
        self.assertEqual(utils.add_disk_sizes('1G', '1K'), '1048577K')
        self.assertEqual(utils.add_disk_sizes('512M', '512M'), '1G')
        self.assertEqual(utils.add_disk_sizes('3800M', '1000M'), '4800M')
