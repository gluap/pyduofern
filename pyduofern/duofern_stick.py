#!/usr/bin/env python3
# coding=utf-8
#   python interface for dufoern usb stick
#   Copyright (C) 2017 Paul Görgen
#   Rough python re-write of the FHEM duofern modules by telekatz, also licensed under GPLv2
#   This re-write contains only negligible amounts of original code
#   apart from some comments to facilitate translation of the not-yet
#   translated parts of the original software. Modification dates are
#   documented as submits to the git repository of this code, currently
#   maintained at https://bitbucket.org/gluap/pyduofern.git

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

import codecs
import json
import logging
import os
import os.path
import threading
import time


def hex(stuff):
    return codecs.getencoder('hex')(stuff)[0].decode("utf-8")


import serial
import serial.tools.list_ports

from .duofern import Duofern
from .exceptions import DuofernTimeoutException, DuofernException

logger = logging.getLogger(__file__)

duoInit1 = "01000000000000000000000000000000000000000000"
duoInit2 = "0E000000000000000000000000000000000000000000"
duoSetDongle = "0Azzzzzz000100000000000000000000000000000000"
duoInit3 = "14140000000000000000000000000000000000000000"
duoSetPairs = "03nnyyyyyy0000000000000000000000000000000000"
duoInitEnd = "10010000000000000000000000000000000000000000"
duoACK = "81000000000000000000000000000000000000000000"
duoStatusRequest = "0DFF0F400000000000000000000000000000FFFFFF01"
duoStartPair = "04000000000000000000000000000000000000000000"
duoStopPair = "05000000000000000000000000000000000000000000"
duoStartUnpair = "07000000000000000000000000000000000000000000"
duoStopUnpair = "08000000000000000000000000000000000000000000"
duoRemotePair = "0D0006010000000000000000000000000000yyyyyy01"


def refresh_serial_connection(function):
    def new_funtion(*args, **kwargs):
        self = args[0]
        if self.serial_connection.isOpen():
            return function(*args, **kwargs)
        else:
            self.serial_connection.open()
            return function(*args, **kwargs)

    return new_funtion


class DuofernStick(threading.Thread):
    def __init__(self, device=None, system_code=None, config_file_json=None, duofern_parser=None):
        """
        
        :param device: path to com port opened by usb stick (e.g. /dev/ttyUSB0)
        :param system_code: system code
        :param config_file_json: path to config file. use the same one to conveniently update info about your system
        :param duofern_parser: parser object. Unless you hacked your own one just leave None and it
         defaults to pyduofern.duofern.Duofern()
        """
        threading.Thread.__init__(self)

        if config_file_json is None:
            config_file_json = "~/.duofern.json"

        if os.path.isfile(config_file_json):
            try:
                with open(config_file_json, "r") as config_file_fh:
                    self.config = json.load(config_file_fh)
            except json.decoder.JSONDecodeError:
                self.config = {'devices': []}
                logger.info('failed reading config')
        else:
            logger.info('config is not file')
            self.config = {'devices': []}

        if duofern_parser is None:
            self.duofern_parser = Duofern(send_hook=self.add_serial_and_send)

        self.running = False
        self.pairing = False
        self.unpairing = False

        if device is None:
            try:
                self.port = serial.tools.list_ports.comports()[0].device
            except IndexError:
                raise DuofernException(
                    "No serial port configured and unable to autodetect device. Did you plug in your stick?")
            logger.debug("no serial port set, autodetected {} for duofern".format(self.port))
        else:
            self.port = device

        if system_code is not None:
            if 'system_code' in self.config:
                assert self.config['system_code'].lower() == system_code.lower(), \
                    'System code passed as argument "{}" differs from config file "{}", please manually change the ' \
                    'config file {} if this is what you intended. If you change the code you paired your devices with' \
                    ' you might have to reset them and re-pair.'.format(system_code,
                                                                        self.config['system_code'],
                                                                        os.path.abspath(config_file_json))

            self.system_code = system_code
        elif 'system_code' in self.config:
            self.system_code = self.config['system_code']
        else:
            raise DuofernException("No system code specified. Since the system code is a security feature no default"
                                   "can be provided. Please re-run wiht a valid system code")

        assert len(self.system_code) == 4, "system code (serial) must be a string of 4 hexadecimal numbers"

        self.serial_connection = serial.Serial(self.port, baudrate=115200, timeout=1)

        self.running = False
        self.pairing = False
        self.unpairing = False
        self.write_queue = []
        self.config_file = config_file_json
        self.config['system_code'] = self.system_code
        self._dump_config()

    def _dump_config(self):
        with open(self.config_file, "w") as config_fh:
            json.dump(self.config, config_fh, indent=4)

    def _initialize(self):  # DoInit
        for i in range(0, 4):
            self._simple_write(duoInit1)
            try:
                self._read_answer("INIT1")
            except DuofernTimeoutException:
                continue

            self._simple_write(duoInit2)
            try:
                self._read_answer("INIT2")
            except DuofernTimeoutException:
                continue

            buf = duoSetDongle.replace("zzzzzz", "6f" + self.system_code)
            self._simple_write(buf)
            try:
                self._read_answer("SetDongle")
            except DuofernTimeoutException:
                continue

            self._simple_write(duoACK)
            self._simple_write(duoInit3)
            try:
                self._read_answer("INIT3")

            except DuofernTimeoutException:
                continue
            self._simple_write(duoACK)
            logger.info(self.config)
            if "devices" in self.config:
                counter = 0
                for device in self.config['devices']:
                    hex_to_write = duoSetPairs.replace('nn', '{:02X}'.format(counter)).replace('yyyyyy', device['id'])
                    self._simple_write(hex_to_write)
                    try:
                        self._read_answer("SetPairs")
                    except DuofernTimeoutException:
                        continue
                    self._simple_write(duoACK)
                    counter += 1
                    self.duofern_parser.add_device(device['id'], device['name'])

            # my counter = 0
            # foreach (@pairs){
            #   buf = duoSetPairs
            #   my chex .= sprintf "%02x", counter
            #   buf =~ s/nn/chex/
            #   buf =~ s/yyyyyy/_/
            #   self._simple_write(buf)
            #   (err, buf) = self._read_answer("SetPairs")
            #   next if(err)
            #   self._simple_write(duoACK)
            #   counter++
            # }

            self._simple_write(duoInitEnd)
            try:
                self._read_answer("INIT3")
            except DuofernTimeoutException:  # look @ original
                return False
            self._simple_write(duoACK)

            self._simple_write(duoStatusRequest)
            try:
                self._read_answer("statusRequest")
            except DuofernTimeoutException:
                continue
            self._simple_write(duoACK)

            # readingsSingleUpdate(hash, "state", "Initialized", 1)
            return True

        raise DuofernTimeoutException("Initialization failed ")

    def _read_answer(self, some_string):  # ReadAnswer
        """read an answer..."""
        logger.debug("should read {}".format(some_string))
        self.serial_connection.timeout = 1
        response = bytearray(self.serial_connection.read(22))

        if len(response) < 22:
            raise DuofernTimeoutException
        logger.debug("response {}".format(hex(response)))
        return hex(response)

    # DUOFERNSTICK_SimpleWrite(@)
    @refresh_serial_connection
    def _simple_write(self, string_to_write):  # SimpleWrite
        """Just write data"""
        logger.debug("writing  {}".format(string_to_write))
        hex_to_write = string_to_write.replace(" ", '')
        data_to_write = bytearray.fromhex(hex_to_write)
        if not self.serial_connection.isOpen():
            self.serial_connection.open()
        self.serial_connection.write(data_to_write)

    def run(self):
        self.running = True
        self._initialize()
        while self.running:
            self.serial_connection.timeout = .05
            if not self.serial_connection.isOpen():
                self.serial_connection.open()
            in_data = hex(self.serial_connection.read(22))
            if len(in_data) == 44:
                if in_data != duoACK:
                    self._simple_write(duoACK)
                try:
                    self.process_message(in_data)
                except Exception as exc:
                    logger.exception(exc)
            self.serial_connection.timeout = 1
            if len(self.write_queue) > 0:
                self.handle_write_queue()

    def process_message(self, message):
        if message[0:2] == '81':
            logger.debug("got Acknowledged")
            # return
            self.handle_write_queue()
            return ()
        if message[0:4] == '0602':
            logger.info("got pairing reply")
            self.pairing = False
            self.duofern_parser.parse(message)
            self.sync_devices()
            return
        # if ($rmsg =~ m / 0602.{40} / ) {
        #    my %addvals = (RAWMSG => $rmsg);
        #    Dispatch($hash, $rmsg, \%addvals) if ($hash->{pair});
        #    delete($hash->{pair});
        #    RemoveInternalTimer($hash);
        #    return undef;
        #
        elif message[0:4] == '0603':
            logger.info("got unpairing reply")
            self.unpairing = False
            self.duofern_parser.parse(message)
            self.sync_devices()
            return
        # } elsif ($rmsg =~ m/0603.{40}/) {
        #    my %addvals = (RAWMSG => $rmsg);
        #    Dispatch($hash, $rmsg, \%addvals) if ($hash->{unpair});
        #    delete($hash->{unpair});
        #    RemoveInternalTimer($hash);
        #    return undef;
        #
        elif message[0:6] == '0FFF11':
            return

        elif message[0:8] == '81000000':
            return
            #  } elsif ($rmsg =~ m/0FFF11.{38}/) {
            #    return undef;
            #
            #  } elsif ($rmsg =~ m/81000000.{36}/) {
            #    return undef;
            #
            #  }
            #
            #  my %addvals = (RAWMSG => $rmsg);
            #  Dispatch($hash, $rmsg, \%addvals);
        #        logger.info("got {}".format(message))
        self.duofern_parser.parse(message)

    def sync_devices(self):
        known_codes = [device['id'].lower() for device in self.config['devices']]
        logger.debug("known codes {}".format(known_codes))
        for module_id in self.duofern_parser.modules['by_code']:
            if module_id.lower() not in known_codes:
                self.config['devices'].append({'id': module_id, 'name': module_id})
            logger.info("paired new device {}".format(module_id))
        self._dump_config()

    def command(self, *args):
        logger.info("sending command")
        logger.info(args)
        return self.duofern_parser.set(*args)

    def set_name(self, id, name):
        logger.info("renaming device {} to {}".format(id, name))
        self.config['devices'] = [device for device in self.config['devices'] if device['id'].lower() != id.lower()]
        self.config['devices'].append({'id': id, 'name': name})
        self._dump_config()
        self._initialize()

    def stop(self):
        self.running = False
        self.serial_connection.close()

    def handle_write_queue(self):
        if len(self.write_queue) > 0:
            tosend = self.write_queue.pop()
            logger.info("sending {} from write queue, {} msgs left in queue".format(tosend, len(self.write_queue)))
            self._simple_write(tosend)

    def send(self, msg):
        logger.info("sending {}".format(msg))
        self.write_queue.append(msg)
        logger.info("added {} to write queueue".format(msg))

    def add_serial_and_send(self, msg):
        message = msg.replace("zzzzzz", "6f" + self.system_code)
        logger.info("sending {}".format(message))
        self.write_queue.append(message)
        logger.info("added {} to write queueue".format(message))

    def stop_pair(self):
        self.write_queue.append(duoStopPair)
        self.pairing = False

    def stop_unpair(self):
        self.write_queue.append(duoStopUnpair)
        self.unpairing = False

    def pair(self, timeout=10):
        self.write_queue.append(duoStartPair)
        threading.Timer(timeout, self.stop_pair).start()
        self.pairing = True

    def unpair(self, timeout=10):
        self.write_queue.append(duoStartUnpair)
        threading.Timer(10, self.stop_unpair).start()
        self.unpairing = True

    def test_callback(self, arg):
        self.duofern_parser.parse(arg)


if __name__ == '__main__':
    formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    test = DuofernStick()
    test._initialize()
    test.start()
    try:
        time.sleep(1)
        test.pair()
        time.sleep(1)
        test.unpair()
        time.sleep(1)
        test.test_callback("argarg")
        for j in range(0, 500):
            try:
                logger.info("waiting")
                time.sleep(1)
            except DuofernTimeoutException:
                pass
    except KeyboardInterrupt:
        test.stop()
        time.sleep(0.1)
        test.join()
