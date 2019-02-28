import logging

# from homeassistant.const import 'serial_port', 'config_file', 'code'
# found advice in the homeassistant creating components manual
# https://home-assistant.io/developers/creating_components/
# Import the device class from the component that you want to support
from homeassistant.components.cover import ATTR_POSITION, CoverDevice

from . import DuofernDevice
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the Awesome Light platform."""

    stick = hass.data[DOMAIN]['stick']

    # Add devices
    for cover in [dev for dev in stick.config['devices'] if not dev['id'].startswith('46')]:
        if cover['id'] not in hass.data[DOMAIN]['unique_ids']:
            hass.data[DOMAIN]['unique_ids'].add(cover['id'])
            add_entities([DuofernShutter(cover['id'], cover['name'], stick, hass)])


class DuofernShutter(DuofernDevice, CoverDevice):
    """Representation of Duofern cover type device."""

    def __init__(self, *args, **kwargs):
        """Initialize the shutter."""
        super().__init__(*args, **kwargs)

    @property
    def current_cover_position(self):
        """Return the display name of this cover."""
        try:
            return 100 - self._stick.duofern_parser.modules['by_code'][self._id]['position']
        except KeyError:
            return None

    @property
    def is_closed(self):
        """Return true if cover is close."""
        try:
            return self._stick.duofern_parser.modules['by_code'][self._id]['position'] == 100
        except KeyError:
            return False

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
