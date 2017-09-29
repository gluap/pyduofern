import asyncio
import logging
import time

import serial_asyncio

logger = logging.getLogger(__name__)
logging.basicConfig(format='pyduofern/%(module)s(%(lineno)d): %(levelname)s %(message)s', level=logging.DEBUG)


# Idee: sleep then flush buffer for resync

# asyncio with sending stuff
# https://stackoverflow.com/questions/30937042/asyncio-persisent-client-protocol-class-using-queue

class Output(asyncio.Protocol):
    def __init__(self, loop):
        self.loop = loop
        self.send_queue = asyncio.Queue()
        self._ready = asyncio.Event()
        self.transport = None
        self.buffer = None
        self.last_packet = 0.0
        self.callback = None
        self.send_loop = asyncio.async(self._send_messages())

    def _initialize(self, future):
        logger.warning("someone called?")
        yield asyncio.sleep(0.1)
        if b'10001               ' in self.buffer:
            future.set_result(True)
        else:
            future.set_result(False)

    def connection_made(self, transport):
        self.transport = transport
        logger.info('port opened {}')
        transport.serial.rts = False
        self.buffer = bytearray(b'')
        self.last_packet = time.time()
        self._ready.set()

    def data_received(self, data):
        if self.last_packet + 0.05 < time.time():
            self.buffer = bytearray(b'')
        self.last_packet = time.time()
        self.buffer += bytearray(data)
        while len(self.buffer) >= 20:
            if self.callback:
                self.callback(self.buffer[0:20])
            else:
                self.parse(self.buffer[0:20])
            self.buffer = self.buffer[20:]

    def pause_writing(self):
        logger.info('pause writing')
        logger.info(self.transport.get_write_buffer_size())

    def resume_writing(self):
        logger.info(self.transport.get_write_buffer_size())
        logger.info('resume writing')

    def parse(self, packet):
        logger.info(packet)

    @asyncio.coroutine
    def send_message(self, data):
        """ Feed a message to the sender coroutine. """
        yield from self.send_queue.put(data)

    @asyncio.coroutine
    def _send_messages(self):
        """ Send messages to the server as they become available. """
        yield from self._ready.wait()
        logger.debug("Starting async send loop!")
        while True:
            try:
                data = yield from self.send_queue.get()
                self.transport.write(data)
            except asyncio.CancelledError:
                logger.info("Got CancelledError, stopping send loop")
                break
            logger.debug("sending {}".format(data))

    def connection_lost(self, exc):
        print('The server closed the connection')
        print('Stop the event loop')

        self.loop.stop()


loop = asyncio.get_event_loop()
coro = serial_asyncio.create_serial_connection(loop, lambda: Output(loop), '/dev/ttyUSB0', baudrate=115200)

f, proto = loop.run_until_complete(coro)


@asyncio.coroutine
def feed_messages(protocol):
    yield from asyncio.sleep(1)
    message = b'----            ----'
    while True:

        future = asyncio.Future(loop=loop)

        def one_time_callback(message):
            if not future.cancelled():
                future.set_result(message)
                protocol.callback = None

        protocol.callback = one_time_callback
        yield from protocol.send_message(message)
        try:
            result = yield from future
            logger.info("awaited future, result: {}".format(result))

        except asyncio.CancelledError:
            logger.info("Got cancelled during initialization sequence")


print("fuckin f: {}".format(f))
print("fuckin proto: {}".format(proto))
try:
    initialization = asyncio.async(feed_messages(proto))
    init = asyncio.wait(initialization)
    logger.info("loop forever")

    loop.run_forever()
except KeyboardInterrupt:
    print('Closing connection')
    initialization.cancel()
    proto.send_loop.cancel()

loop.close()
