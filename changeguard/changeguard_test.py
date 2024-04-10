# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# The ChangeGuard project requires contributions made to this file be licensed
# under the MIT license or a compatible open source license. See LICENSE.md for
# the license text.

import shutil
import tempfile
import unittest
from pathlib import Path

from .changeguard import _FindIgnoreFile


class TestFindIgnoreFile(unittest.TestCase):

  def setUp(self):
    # Create a temporary directory
    self.test_dir = tempfile.mkdtemp()
    self.directory = Path(self.test_dir) / 'path/to/directory'
    self.directory.mkdir(parents=True)

  def tearDown(self):
    # Remove the temporary directory after the test
    shutil.rmtree(self.test_dir)

  def test_find_ignore_file_in_current_directory(self):
    # Create a .changeguard-ignore file in the temporary directory
    ignore_file_path = self.directory / '.changeguard-ignore'
    ignore_file_path.touch()

    result = _FindIgnoreFile(cwd=self.directory)
    self.assertEqual(result, ignore_file_path)

  def test_find_ignore_file_in_parent_directory(self):
    # Create a .changeguard-ignore file in the parent of the temporary directory
    parent_dir = self.directory

    ignore_file_path = parent_dir / '.changeguard-ignore'
    ignore_file_path.touch()

    child_dir = self.directory / 'child'
    child_dir.mkdir()

    result = _FindIgnoreFile(cwd=self.directory)
    self.assertEqual(result, ignore_file_path)

  def test_ignore_file_not_found(self):
    result = _FindIgnoreFile(cwd=self.directory)
    self.assertIsNone(result)


if __name__ == '__main__':
  unittest.main()
