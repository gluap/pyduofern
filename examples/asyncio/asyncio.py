import asyncio
import logging

import serial_asyncio

from pyduofern.duofern_stick import DuofernStickAsync

logging.basicConfig(level=logging.DEBUG)
loop = asyncio.get_event_loop()

coro = serial_asyncio.create_serial_connection(loop, lambda: DuofernStickAsync(loop), '/dev/ttyUSB0', baudrate=115200)
f, proto = loop.run_until_complete(coro)
proto.handshake()

initialization = asyncio.async(proto.handshake())
init = asyncio.wait(initialization)

loop.run_forever()
