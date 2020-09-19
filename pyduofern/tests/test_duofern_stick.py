# coding=utf-8
#   python interface for dufoern usb stick
#   Copyright (C) 2017 Paul Görgen
#   Rough python re-write of the FHEM duofern modules by telekatz, also licensed under GPLv2
#   This re-write contains only negligible amounts of original code
#   apart from some comments to facilitate translation of the not-yet
#   translated parts of the original software. Modification dates are
#   documented as submits to the git repository of this code, currently
#   maintained at https://github.com/gluap/pyduofern.git

#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software Foundation,
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import logging
import tempfile
import time
import unittest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from importlib import reload
from unittest.mock import Mock

import pyduofern.duofern_stick as df


def write_mock(data):
    return True


def read_mock(data):
    return bytearray.fromhex(df.duoACK)


class TestInitialize(unittest.TestCase):
    def setUp(self):
        self.df = reload(df)
        self.df.serial.Serial = Mock()
        # self.df.serial.tools.list_ports.comports()[0].device = "detecteddevice"
        # self.df.serial.Serial.write = write_mock
        # self.df.serial.Serial.read = read_mock

    def test_init(self):
        test = self.df.DuofernStickThreaded(serial_port="bla", system_code="ffff", config_file_json=tempfile.mktemp())
        test.serial_connection = Mock()
        test.serial_connection.read = read_mock
        test._initialize()

    def test_run(self):
        test = self.df.DuofernStickThreaded(serial_port="bla", system_code="ffff", config_file_json=tempfile.mktemp())
        test.serial_connection = Mock()
        test.serial_connection.read = read_mock
        test._initialize()
        test.start()
        time.sleep(0.1)
        test.stop()

    def test_init_recording(self):
        test = self.df.DuofernStickThreaded(serial_port="bla", system_code="ffff", config_file_json=tempfile.mktemp(),
                                            recording=True)
        test.serial_connection = Mock()
        test.serial_connection.read = read_mock
        test._initialize()
