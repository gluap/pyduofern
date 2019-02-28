import logging

# from homeassistant.const import 'serial_port', 'config_file', 'code'
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity

# found advice in the homeassistant creating components manual
# https://home-assistant.io/developers/creating_components/
# Import the device class from the component that you want to support

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['pyduofern==0.24']

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN, DUOFERN_COMPONENTS, CONF_CODE, CONF_SERIAL_PORT

# from . import config_flow

PAIRING_SCHEMA = vol.Schema({
    vol.Optional('timeout', default=30): cv.positive_int,
})


def setup(hass, config):
    """Setup the Awesome Light platform."""

    # Assign configuration variables. The configuration check takes care they are
    # present.

    from pyduofern.duofern_stick import DuofernStickThreaded

    if config.get(DOMAIN) is not None:
        serial_port = config[DOMAIN].get(CONF_SERIAL_PORT)
        if serial_port is None:
            serial_port = "/dev/serial/by-id/usb-Rademacher_DuoFern_USB-Stick_WR04ZFP4-if00-port0"
        code = config[DOMAIN].get(CONF_CODE)
        if code is None:
            code = "affe"
    else:
        raise Exception("duofern needs configuration")

    def refresh():
        hass.data[DOMAIN]['stick'].sync_devices()
        for _component in DUOFERN_COMPONENTS:
            discovery.load_platform(hass, _component, DOMAIN, {}, config)

    hass.data['duofern'] = {
        'stick': DuofernStickThreaded(serial_port=serial_port, system_code=code,
                                      ephemeral=True, changes_callback=refresh),
        'unique_ids': set()}
    hass.data['duofern']['stick'].start()

    # Setup connection with devices/cloud
    stick = hass.data["duofern"]['stick']

    def start_pairing(call):
        hass.data[DOMAIN]['stick'].pair(call)

    hass.services.register(DOMAIN, 'start_pairing', start_pairing, PAIRING_SCHEMA)

    def sync_devices(call):
        refresh()

    hass.services.register(DOMAIN, 'sync_devices', sync_devices)

    refresh()

    return True


class DuofernDevice(Entity):
    """Representation of Duofern cover type device."""

    def __init__(self, id, desc, stick, hass):
        """Initialize the shutter."""
        self._id = id
        self._name = desc
        self._stick = stick
        hass.data[DOMAIN]['unique_ids'].add(id)

    @property
    def name(self):
        return self._name

    @property
    def device_info(self):
        return {
            'identifiers': {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._id)
            },
            'name': self.name,
            'manufacturer': "Rademacher",
            'model': "unknown",
            'sw_version': "unknown",
            # 'via_hub': (hue.DOMAIN, self.api.bridgeid),
        }

    @property
    def unique_id(self):
        return self._id

    def update(self):
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.

        (no new data needs to be fetched, the stick updates itsself in a thread)
        (not the best style for homeassistant, I know. I'll port to asyncio if I find the time)
        """
        pass
        # self._state = True
        # self._brightness = None
