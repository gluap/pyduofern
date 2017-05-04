import time
import unittest
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
        test = self.df.DuofernStick(device="bla")
        test.serial_connection = Mock()
        test.serial_connection.read = read_mock
        test._initialize()

    def test_run(self):
        test = self.df.DuofernStick(device="bla")
        test.serial_connection = Mock()
        test.serial_connection.read = read_mock
        test._initialize()
        test.start()
        time.sleep(0.1)
        test.stop()
