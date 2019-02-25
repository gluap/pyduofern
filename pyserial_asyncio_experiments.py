import asyncio
import logging
import signal
import time

import serial_asyncio

from pyduofern.duofern_stick import duoInit1, duoInit2, duoInit3, duoACK, duoSetDongle

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
        self.send_loop = asyncio.ensure_future(self._send_messages())

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
            if hasattr(self, 'callback') and self.callback is not None:
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

running = True


def one_time_callback(protocol, _message, name, future):
    logger.info("{} answer for {}".format(_message, name))
    if not future.cancelled():
        future.set_result(_message)
        protocol.callback = None

@asyncio.coroutine
def send_and_await_reply(protocol, message, message_identifier):
    future = asyncio.Future()
    protocol.callback = lambda message: one_time_callback(protocol, message, message_identifier, future)
    yield from protocol.send_message(message.encode("utf-8"))
    try:
        result = yield from future
        logger.info("got reply {}".format(result))
    except asyncio.CancelledError:
        logger.info("future was cancelled waiting for reply")


@asyncio.coroutine
def handshake(protocol):
    yield from asyncio.sleep(2)
    HANDSHAKE = [(duoInit1, "INIT1"),
                 (duoInit2, "INIT2"),
                 (duoSetDongle.replace("zzzzzz", "6f" + "affe"), "SetDongle"),
                 (duoACK),
                 (duoInit3, "INIT3")]
    yield from send_and_await_reply(protocol, duoInit1, "init 1")
    yield from send_and_await_reply(protocol, duoInit2, "init 2")
    yield from send_and_await_reply(protocol, duoSetDongle.replace("zzzzzz", "6f" + "affe"), "SetDongle")
    yield from protocol.send_message(duoACK.encode("utf-8"))
    yield from send_and_await_reply(protocol, duoInit3, "init 3")
    yield from protocol.send_message(duoACK.encode("utf-8"))
    logger.info(self.config)
    if "devices" in self.config:
        counter = 0
        for device in self.config['devices']:
            hex_to_write = duoSetPairs.replace('nn', '{:02X}'.format(counter)).replace('yyyyyy', device['id'])
            yield from send_and_await_reply(protocol, hex_to_write, "SetPairs")
            yield from protocol.send_message(duoACK.encode("utf-8"))
            counter += 1
            self.duofern_parser.add_device(device['id'], device['name'])

    yield from send_and_await_reply(protocol, duoInitEnd, "duoInitEnd")
    yield from protocol.send_message(duoACK.encode("utf-8"))
    yield from send_and_await_reply(protocol, duoStatusRequest, "duoInitEnd")
    yield from protocol.send_message(duoACK.encode("utf-8"))


f, proto = loop.run_until_complete(coro)
print("fuckin f: {}".format(f))
print("fuckin proto: {}".format(proto))


def cancelall():
    print('Stopping')
    f.close()
    for task in asyncio.Task.all_tasks():
        task.cancel()


try:
    initialization = asyncio.ensure_future(handshake(proto))
    init = asyncio.wait(initialization)
    logger.info("loop forever")
    loop.add_signal_handler(signal.SIGINT, cancelall)

    loop.run_forever()
except KeyboardInterrupt:
    print('Closing connection')
    initialization.cancel()
finally:
    loop.close()
