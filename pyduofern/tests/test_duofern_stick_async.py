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

import asyncio
import logging

logger = logging.getLogger(__name__)

import serial_asyncio

from unittest.mock import Mock
import pyduofern.duofern_stick  # import DuofernStickAsync

logging.basicConfig(level=logging.DEBUG)
loop = asyncio.get_event_loop()

# coro = serial_asyncio.create_serial_connection(loop, lambda: DuofernStickAsync(loop), '/dev/ttyUSB0', baudrate=115200)
# f, proto = loop.run_until_complete(coro)
# proto.handshake()

proto = pyduofern.duofern_stick.DuofernStickAsync(loop)



class TransportMock(Mock):
    def write(self, data):
        logger.warning("writing {} detected by mock writer".format(data))

def one_time_callback(protocol, _message, name, future):
    logger.info("{} answer for {}".format(_message, name))
    if not future.cancelled():
        future.set_result(_message)
        protocol.callback = None

@asyncio.coroutine
def send_and_await_reply(protocol, message, message_identifier):
    future = asyncio.Future()
    protocol.transport.write = lambda message: one_time_callback(protocol, message, message_identifier, future)
    try:
        result = yield from future
        
    except asyncio.CancelledError:
        logger.info("future was cancelled waiting for reply")


def shakehand(self):
    yield from asyncio.sleep(2)
    logger.info("now handshaking")
    yield from send_and_await_reply(self, duoInit1, "init 1")
    yield from send_and_await_reply(self, duoInit2, "init 2")
    yield from send_and_await_reply(self, duoSetDongle.replace("zzzzzz", "6f" + self.system_code), "SetDongle")
    yield from self.send(duoACK)
    yield from send_and_await_reply(self, duoInit3, "init 3")
    yield from self.send(duoACK)
    logger.info(self.config)
    if "devices" in self.config:
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


proto.transport = TransportMock()
proto._ready = asyncio.Event()
#proto.transport.write = mock_write
initialization = asyncio.async(proto.handshake())
proto._ready.set()




def cb(a):
    logging.info(a)
    #asyncio.async(proto.command("409882", "position", 10))


proto.available.add_done_callback(cb)

#loop.run_forever()
