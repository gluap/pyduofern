import configargparse
import asyncio
import logging
import sys

import serial_asyncio

from distutils.util import strtobool

from asyncio_mqtt import Client


from pyduofern.duofern_stick import DuofernStickAsync

logger = logging.getLogger(__name__)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


async def receive_loop(duo, mqtt_client, updates_received: asyncio.Event, once=False):
    while True:
        await updates_received.wait()
        updates_received.clear()
        logger.info("received event from duofern")
        logger.info(duo.__dict__)


def main(arguments=None):
    loop = asyncio.get_event_loop()
    asyncio.run(_main(arguments))
    # .run(_main, arguments)


async def _main(arguments=None):
    parser = configargparse.ArgumentParser(prog='duofern_mqtt', description='Mqtt connector for pyduofern',
                                           add_config_file_help=True,
                                           default_config_files=['/etc/pyduofern_mqtt.yaml', '~/.pyduofern_mqtt.yaml'],
                                           args_for_setting_config_path=["--config_file"],
                                           config_file_parser_class=configargparse.YAMLConfigFileParser)
    parser.add_argument(
        '--loglevel', default='info', help='Log level',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
    )

    parser.add_argument("--mqtt_server", default="192.168.1.220", help="mqtt server")
    parser.add_argument("--mqtt_port", default=1883, type=int, help="mqtt port")
    parser.add_argument("--mqtt_password", default=None, help="mqtt password")
    parser.add_argument("--mqtt_user", default=None, help="mqtt user")
    parser.add_argument("--serial_port", default=None, help="serial port (e.G. /dev/ttyUSB0) of duofern stick")
    parser.add_argument("--system_code", default=None)

    parser.add_argument("--once", default=False, type=bool, help="no loop, only one pass")

    args = parser.parse_args(arguments)

    change_event = asyncio.Event()

    def notify_change():
        change_event.set()
        logger.info("sending event")

    loop = asyncio.get_running_loop()
    print(args.serial_port)
    transport, proto = await serial_asyncio.create_serial_connection(loop,                                                                lambda: DuofernStickAsync(loop, system_code=args.system_code, ephemeral=True, changes_callback=notify_change), args.serial_port, baudrate=115200)

    initialization = await proto.handshake()
   # f, proto = await duo

    logging.basicConfig(level=args.loglevel.upper())

    async def pair(state: bool):
        if state:
            await proto.pair(timeout=60)
            logger.info("pairing")
        else:
            await proto.stop_pair()
            logger.info("pairing stopped")

    async def unpair(state: bool):
        if state:
            await proto.unpair(timeout=60)
            logger.info("unpairing")
        else:
            await proto.stop_unpair()
            logger.info("unpairing stopped")

    async def handle_control(client, control, path):
        async with client.filtered_messages(path) as messages:
            async for msg in messages:
                logger.info(f"control message received {msg}")
                try:
                    state = strtobool(msg.decode())
                    await control(state)
                except ValueError:
                    logger.warning(f"ignoring incompatible value {msg} for switching")

    if args.mqtt_server is not None:
        async with Client(args.mqtt_server, port=args.mqtt_port, logger=logger, username=args.mqtt_user,
                          password=args.mqtt_password) as client:

            await client.subscribe('/pyduofern/control/#')
            asyncio.create_task(handle_control(client, pair, "/pyduofern/control/start_pairing"))
            asyncio.create_task(handle_control(client, unpair, "/pyduofern/control/start_unpairing"))

            await receive_loop(proto, mqtt_client=client, updates_received=change_event, once=False, )

    else:
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
