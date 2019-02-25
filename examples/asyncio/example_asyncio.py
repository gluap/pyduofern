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
import logging

import serial_asyncio

from pyduofern.duofern_stick import DuofernStickAsync

logging.basicConfig(level=logging.DEBUG)
loop = asyncio.get_event_loop()

coro = serial_asyncio.create_serial_connection(loop, lambda: DuofernStickAsync(loop), '/dev/ttyUSB0', baudrate=115200)
f, proto = loop.run_until_complete(coro)
# proto.handshake()

initialization = asyncio.ensure_future(proto.handshake())
asyncio.wait(initialization)


def cb(a):
    logging.info(a)
    asyncio.ensure_future(proto.command("409882", "position", 10))


proto.available.add_done_callback(cb)


loop.run_forever()
