#!/usr/bin/env python3
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

import asyncio
import codecs
import json
import logging
import os
import os.path
import tempfile
import threading
import time

import serial
import serial.tools.list_ports

from .duofern import Duofern
from .exceptions import DuofernTimeoutException, DuofernException


def hex(stuff):
    return codecs.getencoder('hex')(stuff)[0].decode("utf-8")


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
        else:  # pragma: no cover
            self.serial_connection.open()
            return function(*args, **kwargs)

    return new_funtion


class DuofernStick(object):
    def __init__(self, system_code=None, config_file_json=None, duofern_parser=None, recording=None,
                 changes_callback=None, *args, **kwargs):
        """ 
        :param device: path to com port opened by usb stick (e.g. /dev/ttyUSB0)
        :param system_code: system code
        :param config_file_json: path to config file. use the same one to conveniently update info about your system
        :param duofern_parser: parser object. Unless you hacked your own one just leave None and it
         defaults to pyduofern.duofern.Duofern()
        """
        super().__init__(*args, **kwargs)
        if config_file_json is None:  # pragma: no cover
            config_file_json = os.path.expanduser("~/.duofern.json")

        if os.path.isfile(config_file_json):
            try:
                with open(config_file_json, "r") as config_file_fh:
                    self.config = json.load(config_file_fh)
            except json.decoder.JSONDecodeError:  # pragma: no cover
                self.config = {'devices': []}
                logger.info('failed reading config')
        else:
            logger.info('config is not file')
            self.config = {'devices': []}

        if duofern_parser is None:
            duofern_parser = Duofern(send_hook=self.add_serial_and_send, changes_callback=changes_callback)

        self.duofern_parser = duofern_parser
        self.running = False
        self.pairing = False
        self.unpairing = False

        self.system_code = None
        if system_code is not None:
            if 'system_code' in self.config:
                assert self.config['system_code'].lower() == system_code.lower(), \
                    'System code passed as argument "{}" differs from config file "{}", please manually change the ' \
                    'config file {} if this is what you intended. If you change the code you paired your devices with' \
                    ' you might have to reset them and re-pair.'.format(system_code,
                                                                        self.config['system_code'],
                                                                        os.path.abspath(config_file_json))

            self.system_code = system_code
        elif 'system_code' in self.config:  # pragma: no cover
            self.system_code = self.config['system_code']
        else:
            raise DuofernException("No system code specified. Since the system code is a security feature no default"
                                   "can be provided. Please re-run wiht a valid system code {}".format(self.config))
        assert len(self.system_code) == 4, "system code (serial) must be a string of 4 hexadecimal numbers"

        self.pairing = False
        self.unpairing = False
        self.write_queue = []
        self.config_file = config_file_json
        self.config['system_code'] = self.system_code
        self._dump_config()
        self.initialized = False

        if recording is None and 'recording' in self.config:
            recording = bool(self.config['recording'])

        self.recording = recording
        if recording:
            self._initialize_recording()

    def _initialize_recording(self):
        if 'recording_dir' in self.config:
            dir = self.config['recording_dir']
            assert not os.path.isfile(dir), 'must pass existing or creatable dir as `recording_dir` in config'
            if not os.path.isdir(dir):
                os.makedirs(dir)
            record_filename = os.path.join(dir, "duofern_record_{}".format(str(time.time())))
        else:
            record_filename = tempfile.mktemp(prefix="duofern_record_")
            print("recording to  {}".format(record_filename))
        self.recorder = open(record_filename, 'w')

    def _initialize(self, **kwargs):  # pragma: no cover
        raise NotImplementedError("need to use an implementation of the Duofernstick")

    def _simple_write(self, **kwargs):  # pragma: no cover
        raise NotImplementedError("need to use an implementation of the Duofernstick")

    def send(self, msg, **kwargs):  # pragma: no cover
        raise NotImplementedError("need to use an implementation of the Duofernstick")

    def add_updates_callback(self, callback):
        self.duofern_parser.changes_callback = callback

    def _dump_config(self):
        with open(self.config_file, "w") as config_fh:
            json.dump(self.config, config_fh, indent=4)

    def process_message(self, message):
        if self.recording:
            self.recorder.write("received {}\n".format(message))
            self.recorder.flush()
        if message[0:2] == '81':
            #            logger.debug("got Acknowledged")
            # return
            # self.handle_write_queue()
            return
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

    def set_name(self, id, name):
        logger.info("renaming device {} to {}".format(id, name))
        self.config['devices'] = [device for device in self.config['devices'] if device['id'].lower() != id.lower()]
        self.config['devices'].append({'id': id, 'name': name})
        self._dump_config()
        self._initialize()

    def handle_write_queue(self):
        if len(self.write_queue) > 0:
            tosend = self.write_queue.pop()
            logger.info("sending {} from write queue, {} msgs left in queue".format(tosend, len(self.write_queue)))
            self._simple_write(tosend)

    def stop_pair(self):
        self.send(duoStopPair)
        self.pairing = False

    def stop_unpair(self):
        self.send(duoStopUnpair)
        self.unpairing = False

    def pair(self, timeout=10):
        self.send(duoStartPair)
        threading.Timer(timeout, self.stop_pair).start()
        self.pairing = True

    def unpair(self, timeout=10):
        self.send(duoStartUnpair)
        threading.Timer(10, self.stop_unpair).start()
        self.unpairing = True

    def test_callback(self, arg):
        self.duofern_parser.parse(arg)


def one_time_callback(protocol, _message, name, future):
    logger.info("{} answer for {}".format(_message, name))
    if not future.cancelled():
        future.set_result(_message)
        protocol.callback = None


@asyncio.coroutine
def send_and_await_reply(protocol, message, message_identifier):
    future = asyncio.Future()
    protocol.callback = lambda message: one_time_callback(protocol, message, message_identifier, future)
    yield from protocol.send(message)
    try:
        result = yield from future
        logger.info("got reply {}".format(result))
    except asyncio.CancelledError:
        logger.info("future was cancelled waiting for reply")


class DuofernStickAsync(DuofernStick, asyncio.Protocol):
    def __init__(self, loop=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.duofern_parser.asyncio = True
        self.initialization_step = 0
        self.loop = loop
        self.write_queue = asyncio.Queue()
        self._ready = asyncio.Event()
        self.transport = None
        self.buffer = bytearray(b'')

        self.last_packet = 0.0
        self.callback = None

        if loop == None:
            loop = asyncio.get_event_loop()

        self.send_loop = asyncio.ensure_future(self._send_messages(), loop=loop)

        self.available = asyncio.Future()

        # DuofernStick.__init__(self, device, system_code, config_file_json, duofern_parser)

    #        self.serial_connection = serial.Serial(self.port, baudrate=115200, timeout=1)
    #        self.running = False

    @asyncio.coroutine
    def command(self, *args):
        if self.recording:
            self.recorder.write("sending_command {}\n".format(args))
            self.recorder.flush()
        yield from self.duofern_parser.set(*args)

    def add_serial_and_send(self, msg):
        message = msg.replace("zzzzzz", "6f" + self.system_code)
        logger.info("sending {}".format(message))
        yield from self.send(message)
        logger.info("added {} to write queue".format(message))

    def connection_made(self, transport):
        self.transport = transport
        logger.info('port opened {}')
        transport.serial.rts = False
        self.buffer = bytearray(b'')
        self.last_packet = time.time()
        self._ready.set()

    def data_received(self, data):
        if self.last_packet + 0.05 < time.time() and not hasattr(self.transport, 'unittesting'):
            self.buffer = bytearray(b'')
        self.last_packet = time.time()
        self.buffer += bytearray(data)
        while len(self.buffer) >= 22:
            if self.recording:
                self.recorder.write("received {}\n".format(hex(self.buffer[0:22])))
                self.recorder.flush()
            if not hex(self.buffer[0:22]) == duoACK:
                list(self.send(duoACK))
            if hasattr(self, 'callback') and self.callback is not None:
                self.callback(hex(self.buffer[0:22]))
            elif self.initialized:
                self.process_message(hex(self.buffer[0:22]))
            self.buffer = self.buffer[22:]

    def pause_writing(self):  # pragma: no cover
        logger.info('pause writing')
        logger.info(self.transport.get_write_buffer_size())

    def resume_writing(self):  # pragma: no cover
        logger.info(self.transport.get_write_buffer_size())
        logger.info('resume writing')

    def parse(self, packet):
        logger.info(packet)

    @asyncio.coroutine
    def send(self, data, **kwargs):
        """ Feed a message to the sender coroutine. """
        tosend = bytearray.fromhex(data)
        if self.recording:
            self.recorder.write("sent {}\n".format(data))
            self.recorder.flush()
        yield from self.write_queue.put(tosend)

    @asyncio.coroutine
    def _send_messages(self):
        """ Send messages to the server as they become available. """
        yield from self._ready.wait()
        logger.debug("Starting async send loop!")
        while True:
            try:
                logger.info("sending from stack")
                data = yield from self.write_queue.get()
                self.transport.write(data)
            except asyncio.CancelledError:
                logger.info("Got CancelledError, stopping send loop")
                break
            except Exception as exc:
                raise

    def parse_regular(self, packet):
        logger.info(packet)

    @asyncio.coroutine
    def handshake(self):
        if not hasattr(self.transport, 'unittesting'):
            yield from asyncio.sleep(2)
            logger.info("now handshaking")
        yield from send_and_await_reply(self, duoInit1, "init 1")
        yield from send_and_await_reply(self, duoInit2, "init 2")
        yield from send_and_await_reply(self, duoSetDongle.replace("zzzzzz", "6f" + self.system_code), "SetDongle")
        yield from self.send(duoACK)
        yield from send_and_await_reply(self, duoInit3, "init 3")
        yield from self.send(duoACK)
        if 'devices' in self.config and self.config['devices']:
            counter = 0
            for device in self.config['devices']:
                hex_to_write = duoSetPairs.replace('nn', '{:02X}'.format(counter)).replace('yyyyyy', device['id'])
                yield from send_and_await_reply(self, hex_to_write, "SetPairs")
                yield from self.send(duoACK)
                counter += 1
                self.duofern_parser.add_device(device['id'], device['name'])

        yield from send_and_await_reply(self, duoInitEnd, "duoInitEnd")
        yield from self.send(duoACK)
        yield from send_and_await_reply(self, duoStatusRequest, "duoInitEnd")
        yield from self.send(duoACK)
        self.available.set_result(True)
        self.initialized = True


class DuofernStickThreaded(DuofernStick, threading.Thread):
    def __init__(self, serial_port=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if serial_port is None:
            try:
                self.port = serial.tools.list_ports.comports()[0].device
            except IndexError:
                raise DuofernException(
                    "No serial port configured and unable to autodetect device. Did you plug in your stick?")
            logger.debug("no serial port set, autodetected {} for duofern".format(self.port))
        else:
            self.port = serial_port

        # DuofernStick.__init__(self, device, system_code, config_file_json, duofern_parser)
        self.serial_connection = serial.Serial(self.port, baudrate=115200, timeout=1)
        self.running = False

    def _read_answer(self, some_string):  # ReadAnswer
        """read an answer..."""
        logger.debug("should read {}".format(some_string))
        self.serial_connection.timeout = 1
        response = bytearray(self.serial_connection.read(22))
        if len(response) < 22:
            raise DuofernTimeoutException
        logger.debug("response {}".format(hex(response)))

        if self.recording:
            self.recorder.write("received {}\n".format(hex(response)))
            self.recorder.flush()

        return hex(response)

    def _initialize(self):  # DoInit
        for i in range(0, 4):
            self._simple_write(duoInit1)
            try:
                self._read_answer("INIT1")
            except DuofernTimeoutException:  # pragma: no cover
                continue

            self._simple_write(duoInit2)
            try:
                self._read_answer("INIT2")
            except DuofernTimeoutException:  # pragma: no cover
                continue

            buf = duoSetDongle.replace("zzzzzz", "6f" + self.system_code)
            self._simple_write(buf)
            try:
                self._read_answer("SetDongle")
            except DuofernTimeoutException:  # pragma: no cover
                continue

            self._simple_write(duoACK)
            self._simple_write(duoInit3)
            try:
                self._read_answer("INIT3")

            except DuofernTimeoutException:  # pragma: no cover
                continue
            self._simple_write(duoACK)

            if "devices" in self.config:
                counter = 0
                for device in self.config['devices']:
                    hex_to_write = duoSetPairs.replace('nn', '{:02X}'.format(counter)).replace('yyyyyy', device['id'])
                    self._simple_write(hex_to_write)
                    try:
                        self._read_answer("SetPairs")
                    except DuofernTimeoutException:  # pragma: no cover
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
                self._read_answer("INIT3")  # look @ original?
            except DuofernTimeoutException:  # pragma: no cover
                return False
            self._simple_write(duoACK)

            self._simple_write(duoStatusRequest)
            try:
                self._read_answer("statusRequest")
            except DuofernTimeoutException:  # pragma: no cover
                continue
            self._simple_write(duoACK)

            # readingsSingleUpdate(hash, "state", "Initialized", 1)
            return True

        raise DuofernTimeoutException("Initialization failed ")

    # DUOFERNSTICK_SimpleWrite(@)
    @refresh_serial_connection
    def _simple_write(self, string_to_write):  # SimpleWrite
        """Just write data"""
        logger.debug("writing  {}".format(string_to_write))
        hex_to_write = string_to_write.replace(" ", '')
        if self.recording:
            self.recorder.write("sent {}\n".format(hex_to_write))
            self.recorder.flush()
        data_to_write = bytearray.fromhex(hex_to_write)
        if not self.serial_connection.isOpen():
            self.serial_connection.open()
        self.serial_connection.write(data_to_write)

    def command(self, *args):
        if self.recording:
            self.recorder.write("sending_command {}\n".format(args))
            self.recorder.flush()
        list(self.duofern_parser.set(*args))

    @asyncio.coroutine
    def add_serial_and_send(self, msg):
        message = msg.replace("zzzzzz", "6f" + self.system_code)
        logger.debug("sending {}".format(message))
        yield self.send(message)
        logger.debug("added {} to write queue".format(message))

    def run(self):
        self.running = True
        self._initialize()
        while self.running:
            self.serial_connection.timeout = .05
            if not self.serial_connection.isOpen():
                self.serial_connection.open()
            try:
                in_data = hex(self.serial_connection.read(22))
            except TypeError:
                pass
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

    def stop(self):
        self.running = False
        self.serial_connection.close()

    def pair(self, timeout=10):
        super(DuofernStickThreaded, self).pair(timeout)
        threading.Timer(timeout, self.stop_pair).start()

    def unpair(self, timeout=10):
        super(DuofernStickThreaded, self).unpair(timeout)
        threading.Timer(timeout, self.stop_unpair).start()

    def send(self, msg, **kwargs):
        logger.debug("sending {}".format(msg))
        self.write_queue.append(msg)
        logger.debug("added {} to write queue".format(msg))
        return
