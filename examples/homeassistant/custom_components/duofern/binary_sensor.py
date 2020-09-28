import logging
import math
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_SMOKE,
    PLATFORM_SCHEMA,
    BinarySensorEntity
)

from homeassistant.const import (
    ATTR_BATTERY_LEVEL
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Config validation
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional('serial_port', default=None): cv.string,
    vol.Optional('config_file', default=None): cv.string,
    vol.Optional('code', default=None): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the Duofern binary sensors pltaform"""

    # Get the Duofern stick instance
    stick = hass.data["duofern"]['stick']

    # Add devices
    for device in stick.config['devices']:
        if device['id'].startswith('ab'): # Check if this device is a smoke detector
            if device['id'] in hass.data[DOMAIN]['devices'].keys(): # Check if Home Assistant already has this device
                continue

            add_entities([DuofernSmokeDetector(device['id'], device['name'], stick, hass)]) # Add new binary sensor for smoke detectors


class DuofernSmokeDetector(BinarySensorEntity):
    """Duofern smoke detector entity"""

    def __init__(self, code, desc, stick, hass, channel=None):
        """Initialize the smoke detector"""

        self._code = code
        self._id = code
        self._name = desc

        if channel:
          chanNo = "{:02x}".format(channel)
          self._id += chanNo
          self._name += chanNo

        self._state = None # Holds the state (off = clear, on = smoke detected)
        self._battery_level = None # Holds the battery level of the smoke detector
        self._stick = stick # Hold an instance of the Duofern stick
        self._channel = channel
        hass.data[DOMAIN]['devices'][self._id] = self # Add device to our domain

    @property
    def name(self):
        """Returns the name of the smoke detector"""
        return self._name

    @property
    def is_on(self):
        """Returns the current state of the smoke detector"""
        return self._state == "on"

    @property
    def device_state_attributes(self):
        """Return the battery level of the smoke detector"""
        attributes = {
            ATTR_BATTERY_LEVEL: self._battery_level
        }

        return attributes

    @property
    def icon(self):
        """Return the icon of the smoke detector"""
        return "mdi:smoke-detector"

    @property
    def device_class(self):
        """Return the device class smoke"""
        return DEVICE_CLASS_SMOKE

    @property
    def should_poll(self):
        """Whether this entity should be polled or uses subscriptions"""
        return False # TODO: Add config option for subscriptions over polling

    @property
    def unique_id(self):
        """Return the unique id of the Duofern device"""
        return self._id

    def update(self):
        """Called right before is_on() to update the current state from the stick"""
        try:
            self._state = self._stick.duofern_parser.get_state(self._code, 'state', channel=self._channel)
        except KeyError:
            self._state = None

        try:
            self._battery_level = self._stick.duofern_parser.get_state(self._code, 'batteryLevel', channel=self._channel)
        except KeyError:
            self._battery_level = None
