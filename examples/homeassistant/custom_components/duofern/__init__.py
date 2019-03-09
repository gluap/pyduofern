import logging

# from homeassistant.const import 'serial_port', 'config_file', 'code'
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers import discovery

# found advice in the homeassistant creating components manual
# https://home-assistant.io/developers/creating_components/
# Import the device class from the component that you want to support

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['pyduofern==0.25']

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN, DUOFERN_COMPONENTS, CONF_SERIAL_PORT, CONF_CODE

# Validation of the user's configuration
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({
    vol.Optional('serial_port',                 default="/dev/serial/by-id/usb-Rademacher_DuoFern_USB-Stick_WR04ZFP4-if00-port0"): cv.string,
    vol.Optional('config_file', default=None): cv.string,
    vol.Optional('code', default="deda"): cv.string,
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

    if config.get(DOMAIN) is not None:
        serial_port = config[DOMAIN].get(CONF_SERIAL_PORT)
        if serial_port is None:
            serial_port = "/dev/serial/by-id/usb-Rademacher_DuoFern_USB-Stick_WR04ZFP4-if00-port0"
        code = config[DOMAIN].get(CONF_CODE)
        if code is None:
            code = "affe"
        configfile = config[DOMAIN].get('config_file')

    hass.data[DOMAIN] = {
        'stick': DuofernStickThreaded(serial_port=serial_port, system_code=code, config_file_json=configfile,
                                      ephemeral=True),
        'devices': {}}
    hass.data[DOMAIN]['stick'].start()

    # Setup connection with devices/cloud
    stick = hass.data["duofern"]['stick']

    def start_pairing(call):
        _LOGGER.warning("start pairing")
        hass.data[DOMAIN]['stick'].pair(call.data.get('timeout', 60))

    def start_unpairing(call):
        _LOGGER.warning("start pairing")
        hass.data[DOMAIN]['stick'].unpair(call.data.get('timeout', 60))

    hass.services.register(DOMAIN, 'start_pairing', start_pairing, PAIRING_SCHEMA)
    hass.services.register(DOMAIN, 'start_unpairing', start_unpairing, PAIRING_SCHEMA)

    def sync_devices(call):
        stick.sync_devices()
        _LOGGER.warning(call)
        for _component in DUOFERN_COMPONENTS:
            discovery.load_platform(hass, _component, DOMAIN, {}, config)

    def clean_config(call):
        stick.clean_config()
        stick.sync_cevides()

    hass.services.register(DOMAIN, 'sync_devices', sync_devices)
    hass.services.register(DOMAIN, 'clean_config', sync_devices)


    def refresh(call):
        _LOGGER.warning(call)
        for _component in DUOFERN_COMPONENTS:
            discovery.load_platform(hass, _component, DOMAIN, {}, config)

    for _component in DUOFERN_COMPONENTS:
        discovery.load_platform(hass, _component, DOMAIN, {}, config)

    return True
