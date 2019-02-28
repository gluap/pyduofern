import logging

# from homeassistant.const import 'serial_port', 'config_file', 'code'
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
# found advice in the homeassistant creating components manual
# https://home-assistant.io/developers/creating_components/
# Import the device class from the component that you want to support
from homeassistant.components.light import Light, PLATFORM_SCHEMA

from . import DuofernDevice
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional('serial_port', default=None): cv.string,
    vol.Optional('config_file', default=None): cv.string,
    vol.Optional('code', default=None): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the Awesome Light platform."""

    # Assign configuration variables. The configuration check takes care they are
    # present.

    stick = hass.data["duofern"]['stick']

    # Add devices
    for cover in [dev for dev in stick.config['devices'] if dev['id'].startswith('46')]:
        if cover['id'] not in hass.data[DOMAIN]['unique_ids']:
            hass.data[DOMAIN]['unique_ids'].add(cover['id'])
            add_entities([DuofernLight(cover['id'], cover['name'], stick, hass)])


class DuofernLight(DuofernDevice, Light):
    def __init__(self, *args, **kwargs):
        """Initialize the shutter."""
        super().__init__(*args, **kwargs)

    @property
    def is_on(self):
        try:
            _LOGGER.info(self._stick.duofern_parser.modules['by_code'][self._id])
            return self._stick.duofern_parser.modules['by_code'][self._id]['state'] == "on"
        except KeyError:
            return None

    def turn_on(self):
        self._stick.command(self._id, "on")
        # this is a hotfix because currently the state is not correctly detected from duofern
        self._stick.duofern_parser.modules['by_code'][self._id]['state'] = "on"

    def turn_off(self):
        self._stick.command(self._id, "off")
        # this is a hotfix because currently the state is not correctly detected from duofern
        self._stick.duofern_parser.modules['by_code'][self._id]['state'] = 0
