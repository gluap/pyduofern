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
    for device in stick.config['devices']:
        if device['id'].startswith('46') or device['id'].startswith('48'):
            if device['id'] in hass.data[DOMAIN]['devices'].keys():
                continue
            add_devices([DuofernLight(device['id'], device['name'], stick, hass)])

        if device['id'].startswith('43'):
            for channel in [1,2]:
                chanNo = "{:02x}".format(channel)
                if device['id']+chanNo in hass.data[DOMAIN]['devices'].keys():
                    continue
                add_devices([DuofernLight(device['id'], device['name'], stick, hass, channel=channel)])

class DuofernLight(Light):
    def __init__(self, code, desc, stick, hass, channel=None):
        """Initialize the light."""
        self._code = code
        self._id = code
        self._name = desc

        if channel:
          chanNo = "{:02x}".format(channel)
          self._id += chanNo
          self._name += chanNo

        self._state = None
        self._brightness = None
        self._stick = stick
        self._channel = channel
        hass.data[DOMAIN]['devices'][self._id] = self

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        try:
            _LOGGER.info(self._stick.duofern_parser.modules['by_code'][self._code])
            state = self._stick.duofern_parser.get_state(self._code, 'state', channel=self._channel)
            return state == "on"
        except KeyError:
            return None

    @property
    def unique_id(self):
        return self._id

    def turn_on(self):
        self._stick.command(self._code, "on", channel=self._channel)
        # this is a hotfix because currently the state is detected with delay from duofern
        self._stick.duofern_parser.update_state(self._code, 'state', "on", channel=self._channel)

    def turn_off(self):
        self._stick.command(self._code, "off", channel=self._channel)
        # this is a hotfix because currently the state is detected with delay from duofern
        self._stick.duofern_parser.update_state(self._code, 'state', "off", channel=self._channel)

    def update(self):
        pass
