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
Tests for miscellaneous utility methods.
"""

import unittest

from freedommaker import utils


class TestUtils(unittest.TestCase):
    """Test for miscellaneous utility methods."""
    def test_add_disk_offsets(self):
        """Test disk offset addition."""
        self.assertEqual(utils.add_disk_offsets('1mib', '2mib'), '3mib')
        self.assertRaises(NotImplementedError, utils.add_disk_offsets, '1gib',
                          '1mib')
        self.assertRaises(NotImplementedError, utils.add_disk_offsets, '1mib',
                          '1gib')
        self.assertRaises(ValueError, utils.add_disk_offsets, 'xmib', '1mib')
        self.assertRaises(ValueError, utils.add_disk_offsets, 'xmib', 'xmib')

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
