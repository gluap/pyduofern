import logging
import os
import time

# from homeassistant.const import 'serial_port', 'config_file', 'code'
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers import discovery

# found advice in the homeassistant creating components manual
# https://home-assistant.io/developers/creating_components/
# Import the device class from the component that you want to support

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['pyduofern==0.34.0']

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN, DUOFERN_COMPONENTS, CONF_SERIAL_PORT, CONF_CODE

# Validation of the user's configuration
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({
    vol.Optional('serial_port',
                 default="/dev/serial/by-id/usb-Rademacher_DuoFern_USB-Stick_WR04ZFP4-if00-port0"): cv.string,
    vol.Optional('config_file', default=os.path.join(os.path.dirname(__file__), "../../duofern.json")): cv.string,
    # config file: default to homeassistant config directory (assuming this is a custom component)
    vol.Optional('code', default="0000"): cv.string,
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

    newstyle_config = hass.config_entries.async_entries(DOMAIN)
    if len(newstyle_config) > 0:
        newstyle_config = newstyle_config[0]
        if newstyle_config:
            serial_port = newstyle_config.data['serial_port']
            code = newstyle_config.data['code']
            configfile = newstyle_config.data['config_file']

    elif config.get(DOMAIN) is not None:
        serial_port = config[DOMAIN].get(CONF_SERIAL_PORT)
        if serial_port is None:
            serial_port = "/dev/serial/by-id/usb-Rademacher_DuoFern_USB-Stick_WR04ZFP4-if00-port0"
        code = config[DOMAIN].get(CONF_CODE, None)
        if code is None:
            code = "affe"
        configfile = config[DOMAIN].get('config_file')

    hass.data[DOMAIN] = {
        'stick': DuofernStickThreaded(serial_port=serial_port, system_code=code, config_file_json=configfile,
                                      ephemeral=False),
        'devices': {}}

    # Setup connection with devices/cloud
    stick = hass.data[DOMAIN]['stick']

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
        stick.sync_devices()

    hass.services.register(DOMAIN, 'sync_devices', sync_devices)
    hass.services.register(DOMAIN, 'clean_config', clean_config)

    def refresh(call):
        _LOGGER.warning(call)
        for _component in DUOFERN_COMPONENTS:
            discovery.load_platform(hass, _component, DOMAIN, {}, config)

    for _component in DUOFERN_COMPONENTS:
        discovery.load_platform(hass, _component, DOMAIN, {}, config)

    def update_callback(id, key, value):
        if id is not None:
            try:
                device = hass.data[DOMAIN]['devices'][id] # Get device by id
                if not device.should_poll: # Only trigger update if this entity is not polling
                    try:
                        device.schedule_update_ha_state(True) # Trigger update on the updated entity
                    except AssertionError:
                        _LOGGER.warning("Update callback called before HA is ready") # Trying to update before HA is ready
            except KeyError:
                _LOGGER.warning("Update callback called on unknown device id") # Ignore invalid device ids

    stick.add_updates_callback(update_callback)

    time.sleep(5) # Wait for 5 seconds so HA can get our entities ready so we don't miss any updates (there are probably nicer ways to do this)
    stick.start() # Start the stick after 5 seconds

    return True
