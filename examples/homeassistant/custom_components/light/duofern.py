import logging

# from homeassistant.const import 'serial_port', 'config_file', 'code'
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
# found advice in the homeassistant creating components manual
# https://home-assistant.io/developers/creating_components/
# Import the device class from the component that you want to support
from homeassistant.components.light import Light, PLATFORM_SCHEMA

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['pyduofern==0.23.5']

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

    from pyduofern.duofern_stick import DuofernStickThreaded

    serial_port = config.get('serial_port')
    code = config.get('code')
    configfile = config.get('config_file')

    if 'duofern' not in hass.data:
        hass.data['duofern'] = {
            'stick': DuofernStickThreaded(serial_port=serial_port, system_code=code, config_file_json=configfile)}
        hass.data['duofern']['stick'].start()
        # Setup connection with devices/cloud
    stick = hass.data["duofern"]['stick']

    # Add devices
    add_devices(DuofernLight(device['id'], device['name'], stick) for device in stick.config['devices'] if
                device['id'].startswith('46'))


class DuofernLight(Light):
    def __init__(self, id, desc, stick):
        """Initialize the shutter."""
        self._id = id
        self._name = desc
        self._state = None
        self._brightness = None
        self._stick = stick

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
