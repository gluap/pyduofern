import logging

# from homeassistant.const import 'serial_port', 'config_file', 'code'
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers import discovery

# found advice in the homeassistant creating components manual
# https://home-assistant.io/developers/creating_components/
# Import the device class from the component that you want to support

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['pyduofern==0.23.5']

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN, DUOFERN_COMPONENTS

# Validation of the user's configuration
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({
    vol.Optional('serial_port', default=None): cv.string,
    vol.Optional('config_file', default=None): cv.string,
    vol.Optional('code', default=None): cv.string,
}),
}, extra=vol.ALLOW_EXTRA)

PAIRING_SCHEMA = vol.Schema({
    vol.Optional('timeout', default=30): cv.positive_int,
})


def setup(hass, config):
    """Setup the Awesome Light platform."""

    # Assign configuration variables. The configuration check takes care they are
    # present.

    from pyduofern.duofern_stick import DuofernStickThreaded

    serial_port = config.get('serial_port')
    code = config.get('code')
    configfile = config.get('config_file')
    hass.data['duofern'] = {
        'stick': DuofernStickThreaded(serial_port=serial_port, system_code=code, config_file_json=configfile,
                                      ephemeral=True)}
    hass.data['duofern']['stick'].start()

    # Setup connection with devices/cloud
    stick = hass.data["duofern"]['stick']

    def start_pairing(call):
        _LOGGER.warning("start pairing")
        hass.data[DOMAIN]['stick'].pair(call)

    hass.services.register(DOMAIN, 'start_pairing', start_pairing, PAIRING_SCHEMA)

    def sync_devices(call):
        stick.sync_devices()
        _LOGGER.warning(call)
        for _component in DUOFERN_COMPONENTS:
            discovery.load_platform(hass, _component, DOMAIN, {}, config)

    hass.services.register(DOMAIN, 'sync_devices', sync_devices)

    def refresh(call):
        _LOGGER.warning(call)
        for _component in DUOFERN_COMPONENTS:
            discovery.load_platform(hass, _component, DOMAIN, {}, config)

    for _component in DUOFERN_COMPONENTS:
        discovery.load_platform(hass, _component, DOMAIN, {}, config)

    return True
