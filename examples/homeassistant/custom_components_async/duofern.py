import asyncio
import logging

# from homeassistant.const import 'serial_port', 'config_file', 'code'
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers import discovery

from pyduofern.duofern_stick import DuofernStickAsync

DOMAIN = 'duofern'

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['pyduofern==0.23.5']

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
CONFIG_SCHEMA = vol.Schema({
    vol.Optional('serial_port', default=None): cv.string,
    vol.Optional('config_file', default=None): cv.string,
    vol.Optional('code', default=None): cv.string,
})


async def async_setup(hass, config):
    """Setup the duofern platform."""

    serial_port = config.get('serial_port')
    code = config.get('code')
    configfile = config.get('config_file')

    hass.data['duofern'] = {
        'stick': DuofernStickAsync(serial_port=serial_port, system_code=code, config_file_json=configfile)}
    hass.loop.create_task(hass.data['duofern']['stick'].handshake())

    # wait for handshake done (via future)
    await hass.data['duofern']['stick'].available

    # wait for a bit to allow duofern devices to call in
    await asyncio.sleep(10)

    hass.async_add_job(discovery.async_load_platform(hass, 'cover', DOMAIN, {}, config))
#    hass.async_add_job(discovery.async_load_platform(hass, 'sensor', DOMAIN, {}, config))
