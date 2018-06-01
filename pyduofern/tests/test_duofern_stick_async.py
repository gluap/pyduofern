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
logger.setLevel(logging.INFO)

from unittest.mock import Mock
import pyduofern.duofern_stick  # import DuofernStickAsync

logging.basicConfig(level=logging.DEBUG)
loop = asyncio.get_event_loop()

# coro = serial_asyncio.create_serial_connection(loop, lambda: DuofernStickAsync(loop), '/dev/ttyUSB0', baudrate=115200)
# f, proto = loop.run_until_complete(coro)
# proto.handshake()

proto = pyduofern.duofern_stick.DuofernStickAsync(loop, system_code="ffff")



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


def test_init_against_mocked_stick():
    proto.transport = TransportMock()
    proto._ready = asyncio.Event()
    # proto.transport.write = mock_write
    initialization = asyncio.async(proto.handshake())
    proto._ready.set()

    def cb(a):
        logging.info(a)

    proto.available.add_done_callback(cb)
