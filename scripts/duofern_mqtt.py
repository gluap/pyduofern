import asyncio
import configargparse
import logging
import json
import sys
import aiohttp.client_exceptions

from asyncio_mqtt import Client
import asyncio_mqtt.error

from distutils.util import strtobool

from pyess.aio_ess import ESS
from pyess.ess import autodetect_ess

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


async def recursive_publish_dict(mqtt_client, publish_root, dictionary):
    for key, value in dictionary.items():
        if isinstance(value, dict):
            await recursive_publish_dict(mqtt_client, f"{publish_root}/{key}", value)
        else:
            try:
                await mqtt_client.publish(f"{publish_root}/{key}", value)
            except (asyncio_mqtt.error.MqttCodeError, TimeoutError): # pragma: no cover
                logger.warning("Lost MQTT connection to mqtt errorcode or timeout, restarting", exc_info=True)
                raise
            except:  # pragma: no cover
                logger.exception(f"Lost MQTT connection to unexpected error code, restarting", exc_info=True)
                raise


async def send_loop(ess, mqtt_client=None, graphite_client=None, once=False, interval_seconds=10, common_divisor=1):
    logger.info("starting send loop")
    i = 0
    while True:
        if not once:
            await asyncio.sleep(1)
        home = await ess.get_state("home")
        await recursive_publish_dict(mqtt_client, "ess/home", home)

        if i % common_divisor == 0:
            common = await ess.get_state("common")
            await recursive_publish_dict(mqtt_client, "ess/common", common)

        i += 1
        if once:
            break
        await asyncio.sleep(interval_seconds - 1)


def prepare_description(sensor):
    description = {"name": sensor, "state_topic": sensor}
    if "power" in sensor:
        description["device_class"] = "power"
        description["unit_of_measurement"] = "W"
    if "enegy" in sensor or "energy" in sensor:  # typo in ess json
        description["unit_of_measuremnt"] = "Wh"
        description["icon"] = "mdi:gauge"
    if "soc" in sensor:
        description["device_class"] = "battery"
    if "current" in sensor:
        description["unit_of_measurement"] = "A"
        description["icon"] = "mdi:gauge"
    if "voltage" in sensor:
        description["unit_of_measurement"] = "V"
        description["icon"] = "mdi:gauge"
    return description


async def announce_loop(client, sensors=None):
    if sensors is None:
        return

    for sensor in sensors:
        try:
            await client.publish(f"homeassistant/sensor/{sensor.replace('/', '')}/config",
                                 json.dumps(prepare_description(sensor)), retain=True, qos=2)
        except (asyncio_mqtt.error.MqttCodeError, TimeoutError): # pragma: no cover
            logger.warning("Lost MQTT connection to mqtt errorcode in announce loop, send loop will exit")
        except:  # pragma: no cover
            logger.exception(f"Lost MQTT connection to unexpected error code, restarting", exc_info=True)
            raise


def main(arguments=None):
    loop = asyncio.get_event_loop()
    asyncio.run(_main(arguments))
    # .run(_main, arguments)


async def _main( arguments=None):
    loop = asyncio.get_event_loop()
    parser = configargparse.ArgumentParser(prog='essmqtt', description='Mqtt connector for pyess',
                                           add_config_file_help=True,
                                           default_config_files=['/etc/essmqtt.conf', '~/.essmqtt.conf'],
                                           args_for_setting_config_path=["--config_file"], )

    parser.add_argument(
        '--loglevel', default='info', help='Log level',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
    )

    parser.add_argument("--ess_password", default=None, help="password (required for everything but get_password)")
    parser.add_argument("--mqtt_server", default="192.168.1.220", help="mqtt server")
    parser.add_argument("--mqtt_port", default=1883, type=int, help="mqtt port")
    parser.add_argument("--mqtt_password", default=None, help="mqtt password")
    parser.add_argument("--mqtt_user", default=None, help="mqtt user")
    parser.add_argument("--ess_host", default=None, help="hostname or IP of mqtt host (discover via mdns if not set)")
    parser.add_argument("--once", default=False, type=bool, help="no loop, only one pass")
    parser.add_argument("--common_divisor", default=1, type=int,
                        help="multiply interval_seconds for values below 'common' by this factor")
    parser.add_argument("--interval_seconds", default=10, type=int, help="update interval (default: 10 seconds)")
    parser.add_argument("--hass_autoconfig_sensors", default=None, help="comma-separated list of sensors to advertise"
                                                                        "for homassistant autconfig")

    args = parser.parse_args(arguments)
    if args.ess_host is None:
        ip, name = await loop.run_in_executor(None, autodetect_ess)
    else:
        ip, name = args.ess_host, args.ess_host

    logging.basicConfig(level=args.loglevel.upper())

    ess = await ESS.create(name, args.ess_password, ip)

    async def switch_winter(state: bool):
        logger.info(f"switching winter mode to {state}")
        if state:
            await ess.winter_off()
        else:
            await ess.winter_on()

    async def switch_fastcharge(state: bool):
        logger.info(f"switching fast charge mode to {state}")
        if state:
            await ess.fastcharge_on()
        else:
            await ess.fastcharge_off()

    async def switch_active(state: bool):
        logger.info("switching ess {}".format("on" if state else "off"))
        if state:
            await ess.switch_on()
        else:
            await ess.switch_off()

    async def handle_control(client, control, path):
        async with client.filtered_messages(path) as messages:
            async for msg in messages:
                logger.info(f"control message received {msg}")
                try:
                    state = strtobool(msg.payload.decode())
                    await control(state)
                except ValueError:
                    logger.warning(f"ignoring incompatible value {msg} for switching")

    if args.mqtt_server is not None:
        while True:
            try:
                await launch_main_loop(args, ess, handle_control, switch_active, switch_fastcharge, switch_winter)
            except (TimeoutError, asyncio_mqtt.error.MqttCodeError, aiohttp.client_exceptions.ClientError,
                    BrokenPipeError,  ConnectionError):
                logger.warning("Expected exception while talking go ESS or MQTT server, restarting in 60 seconds."
                               "Usually this means the server is slow to respond or unreachable.")
                await asyncio.sleep(60)
            except:
                raise

            ess = await ESS.create(name, args.ess_password, ip)

            if args.once:
                break

    else:
        pass


async def launch_main_loop(args, ess, handle_control, switch_active, switch_fastcharge, switch_winter):
    async with Client(args.mqtt_server, port=args.mqtt_port, logger=logger, username=args.mqtt_user,
                      password=args.mqtt_password) as client:
        # seems that a leading slash is frowned upon in mqtt, but we keep this for backwards compatibility
        await client.subscribe('/ess/control/#')
        asyncio.create_task(handle_control(client, switch_winter, "/ess/control/winter_mode"))
        asyncio.create_task(handle_control(client, switch_fastcharge, "/ess/control/fastcharge"))
        asyncio.create_task(handle_control(client, switch_active, "/ess/control/active"))

        # also subscribe without leading slash for better style
        await client.subscribe('ess/control/#')
        asyncio.create_task(handle_control(client, switch_winter, "ess/control/winter_mode"))
        asyncio.create_task(handle_control(client, switch_fastcharge, "ess/control/fastcharge"))
        asyncio.create_task(handle_control(client, switch_active, "ess/control/active"))
        if args.hass_autoconfig_sensors is not None:
            asyncio.ensure_future(
                announce_loop(client, sensors=args.hass_autoconfig_sensors.split(",")))

        await send_loop(ess, client, once=args.once, interval_seconds=args.interval_seconds,
                        common_divisor=args.common_divisor)


if __name__ == "__main__":
    main(sys.argv[1:])
