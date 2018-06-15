import logging

# from homeassistant.const import 'serial_port', 'config_file', 'code'
# found advice in the homeassistant creating components manual
# https://home-assistant.io/developers/creating_components/
# Import the device class from the component that you want to support
from homeassistant.components.cover import ATTR_POSITION, CoverDevice
from homeassistant.core import callback

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['pyduofern']

from pyduofern.duofern_stick import DuofernStickThreaded

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Awesome Light platform."""

    # Assign configuration variables. The configuration check takes care they are
    # present.
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
    add_devices(DuofernShutter(device['id'], device['name'], stick) for device in stick.config['devices'] if
                not device['id'].startswith('46'))


class DuofernShutter(CoverDevice):
    """Representation of Duofern cover type device."""

    def __init__(self, id, desc, stick):
        """Initialize the shutter."""
        self._id = id
        self._name = desc
        self._state = None
        self._brightness = None
        self._stick = stick
        self.opening = False
        self.closing = False
        self._stick.add_callback(self.update)

    @property
    def name(self):
        return self._name

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

    @property
    def is_opening(self):
        return self.opening

    @property
    def is_closing(self):
        return self.closing

    async def async_open_cover(self):
        """roll up cover"""
        yield self._stick.command(self._id, "up")

    async def async_close_cover(self):
        """close cover"""
        yield self._stick.command(self._id, "down")

    async def async_stop_cover(self):
        """stop cover"""
        self._stick.command(self._id, "stop")

    async def async_set_cover_position(self, **kwargs):
        """set position (100-position to make the default intuitive: 0%=closed, 100%=open"""

        position = kwargs.get(ATTR_POSITION)
        if position > self.current_cover_position:
            self.opening = True
        elif position < self.current_cover_position:
            self.closing = True

        yield self._stick.command(self._id, "position", 100 - position)

    @callback
    def update(self):
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        
        (no new data needs to be fetched, the stick updates itsself in a thread)
        (not the best style for homeassistant, I know. I'll port to asyncio if I find the time)
        """

        self.async_schedule_update_ha_state()


class TradfriLight(Light):
    """The platform class required by Home Assistant."""

    def __init__(self, light, api, gateway_id):
        """Initialize a Light."""
        self._api = api
        self._unique_id = "light-{}-{}".format(gateway_id, light.id)
        self._light = None
        self._light_control = None
        self._light_data = None
        self._name = None
        self._hs_color = None
        self._features = SUPPORTED_FEATURES
        self._available = True

        self._refresh(light)

    @property
    def unique_id(self):
        """Return unique ID for light."""
        return self._unique_id

    @property
    def min_mireds(self):
        """Return the coldest color_temp that this light supports."""
        return self._light_control.min_mireds

    @property
    def max_mireds(self):
        """Return the warmest color_temp that this light supports."""
        return self._light_control.max_mireds

    async def async_added_to_hass(self):
        """Start thread when added to hass."""
        self._async_start_observe()

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    @property
    def should_poll(self):
        """No polling needed for tradfri light."""
        return False

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._features

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._light_data.state

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._light_data.dimmer

    @property
    def color_temp(self):
        """Return the color temp value in mireds."""
        return self._light_data.color_temp

    @property
    def hs_color(self):
        """HS color of the light."""
        if self._light_control.can_set_color:
            hsbxy = self._light_data.hsb_xy_color
            hue = hsbxy[0] / (65535 / 360)
            sat = hsbxy[1] / (65279 / 100)
            if hue is not None and sat is not None:
                return hue, sat

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        await self._api(self._light_control.set_state(False))

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        params = {}
        transition_time = None
        if ATTR_TRANSITION in kwargs:
            transition_time = int(kwargs[ATTR_TRANSITION]) * 10

        brightness = kwargs.get(ATTR_BRIGHTNESS)

        if brightness is not None:
            if brightness > 254:
                brightness = 254
            elif brightness < 0:
                brightness = 0

        if ATTR_HS_COLOR in kwargs and self._light_control.can_set_color:
            params[ATTR_BRIGHTNESS] = brightness
            hue = int(kwargs[ATTR_HS_COLOR][0] * (65535 / 360))
            sat = int(kwargs[ATTR_HS_COLOR][1] * (65279 / 100))
            if brightness is None:
                params[ATTR_TRANSITION_TIME] = transition_time
            await self._api(
                self._light_control.set_hsb(hue, sat, **params))
            return

        if ATTR_COLOR_TEMP in kwargs and (self._light_control.can_set_temp or
                                          self._light_control.can_set_color):
            temp = kwargs[ATTR_COLOR_TEMP]
            if temp > self.max_mireds:
                temp = self.max_mireds
            elif temp < self.min_mireds:
                temp = self.min_mireds

            if brightness is None:
                params[ATTR_TRANSITION_TIME] = transition_time
            # White Spectrum bulb
            if (self._light_control.can_set_temp and
                    not self._light_control.can_set_color):
                await self._api(
                    self._light_control.set_color_temp(temp, **params))
            # Color bulb (CWS)
            # color_temp needs to be set with hue/saturation
            if self._light_control.can_set_color:
                params[ATTR_BRIGHTNESS] = brightness
                temp_k = color_util.color_temperature_mired_to_kelvin(temp)
                hs_color = color_util.color_temperature_to_hs(temp_k)
                hue = int(hs_color[0] * (65535 / 360))
                sat = int(hs_color[1] * (65279 / 100))
                await self._api(
                    self._light_control.set_hsb(hue, sat,
                                                **params))

        if brightness is not None:
            params[ATTR_TRANSITION_TIME] = transition_time
            await self._api(
                self._light_control.set_dimmer(brightness,
                                               **params))
        else:
            await self._api(
                self._light_control.set_state(True))

    @callback
    def _async_start_observe(self, exc=None):
        """Start observation of light."""
        # pylint: disable=import-error
        from pytradfri.error import PytradfriError
        if exc:
            _LOGGER.warning("Observation failed for %s", self._name,
                            exc_info=exc)

        try:
            cmd = self._light.observe(callback=self._observe_update,
                                      err_callback=self._async_start_observe,
                                      duration=0)
            self.hass.async_add_job(self._api(cmd))
        except PytradfriError as err:
            _LOGGER.warning("Observation failed, trying again", exc_info=err)
            self._async_start_observe()

    def _refresh(self, light):
        """Refresh the light data."""
        self._light = light

        # Caching of LightControl and light object
        self._available = light.reachable
        self._light_control = light.light_control
        self._light_data = light.light_control.lights[0]
        self._name = light.name
        self._features = SUPPORTED_FEATURES

        if light.light_control.can_set_color:
            self._features |= SUPPORT_COLOR
        if light.light_control.can_set_temp:
            self._features |= SUPPORT_COLOR_TEMP

    @callback
    def _observe_update(self, tradfri_device):
        """Receive new state data for this light."""
        self._refresh(tradfri_device)
