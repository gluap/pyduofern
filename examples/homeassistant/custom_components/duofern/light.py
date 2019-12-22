import logging

# from homeassistant.const import 'serial_port', 'config_file', 'code'
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
# found advice in the homeassistant creating components manual
# https://home-assistant.io/developers/creating_components/
# Import the device class from the component that you want to support
from homeassistant.components.light import Light, PLATFORM_SCHEMA

# Home Assistant depends on 3rd party packages for API specific code.

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional('serial_port', default=None): cv.string,
    vol.Optional('config_file', default=None): cv.string,
    vol.Optional('code', default=None): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Awesome Light platform."""

    # Assign configuration variables. The configuration check takes care they are
    # present.

    stick = hass.data["duofern"]['stick']

    # Add devices
    to_add = [DuofernLight(device['id'], device['name'], stick, hass) for device in stick.config['devices'] if
              (device['id'].startswith('46') or (device['id'].startswith('43') and len(device['id']) == 8)) and not device['id'] in hass.data[DOMAIN]['devices'].keys()]
    add_devices(to_add)


class DuofernLight(Light):
    def __init__(self, id, desc, stick, hass):
        """Initialize the shutter."""
        self._id = id
        self._name = desc
        self._state = None
        self._brightness = None
        self._stick = stick
        hass.data[DOMAIN]['devices'][id] = self

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        try:
            _LOGGER.info(self._stick.duofern_parser.modules['by_code'][self._id])
            return self._stick.duofern_parser.modules['by_code'][self._id]['state'] == "on"
        except KeyError:
            return None

    @property
    def unique_id(self):
        return self._id

    def turn_on(self):
        self._stick.command(self._id, "on")
        # this is a hotfix because currently the state is not correctly detected from duofern
        self._stick.duofern_parser.modules['by_code'][self._id]['state'] = "on"

    def turn_off(self):
        self._stick.command(self._id, "off")
        # this is a hotfix because currently the state is not correctly detected from duofern
        self._stick.duofern_parser.modules['by_code'][self._id]['state'] = 0

    def update(self):
        pass
