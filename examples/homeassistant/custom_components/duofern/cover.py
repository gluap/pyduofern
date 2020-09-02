import logging

# from homeassistant.const import 'serial_port', 'config_file', 'code'
# found advice in the homeassistant creating components manual
# https://home-assistant.io/developers/creating_components/
# Import the device class from the component that you want to support
from homeassistant.components.cover import ATTR_POSITION, CoverEntity

from .const import DOMAIN

# Home Assistant depends on 3rd party packages for API specific code.

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Awesome Light platform."""

    stick = hass.data[DOMAIN]['stick']

    # Add devices
    to_add = [DuofernShutter(device['id'], device['name'], stick, hass) for device in stick.config['devices'] if (device['id'].startswith('40') or device['id'].startswith('41') or device['id'].startswith('42') or device['id'].startswith('47') or device['id'].startswith('49') or device['id'].startswith('61')) and not device['id'] in hass.data[DOMAIN]['devices'].keys()]
    add_devices(to_add)


class DuofernShutter(CoverEntity):
    """Representation of Duofern cover type device."""

    def __init__(self, id, desc, stick, hass):
        """Initialize the shutter."""
        self._id = id
        self._name = desc
        self._state = None
        self._stick = stick
        hass.data[DOMAIN]['devices'][id] = self

    @property
    def name(self):
        return self._name

    @property
    def current_cover_position(self):
        """Return the display name of this cover."""
        return self._state

    @property
    def is_closed(self):
        """Return true if cover is close."""
        return self._state == 100

    @property
    def should_poll(self):
        """Whether this entity should be polled or uses subscriptions"""
        return False # TODO: Add config option for subscriptions over polling

    @property
    def unique_id(self):
        return self._id

    def open_cover(self):
        """roll up cover"""
        self._stick.command(self._id, "up")

    def close_cover(self):
        """close cover"""
        self._stick.command(self._id, "down")

    def stop_cover(self):
        """stop cover"""
        self._stick.command(self._id, "stop")

    def set_cover_position(self, **kwargs):
        """set position (100-position to make the default intuitive: 0%=closed, 100%=open"""
        position = kwargs.get(ATTR_POSITION)
        self._stick.command(self._id, "position", 100 - position)

    def update(self):
        """Fetch new state data for this cover.

        This is the only method that should fetch new data for Home Assistant.

        (no new data needs to be fetched, the stick updates itsself in a thread)
        (not the best style for homeassistant, I know. I'll port to asyncio if I find the time)
        """
        try:
            self._state = 100 - self._stick.duofern_parser.modules['by_code'][self._id]['position']
        except KeyError:
            self._state = None
