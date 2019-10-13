import os

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


class DomainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for duofern."""

    CONNECTION_CLASS = config_entries.CONN_CLASS_UNKNOWN

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title='duofern', data=user_input
            )

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required('code'): str,
                vol.Optional('serial_port',
                             default="/dev/serial/by-id/usb-Rademacher_DuoFern_USB-Stick_WR04ZFP4-if00-port0"): str,
                vol.Optional('config_file', default=os.path.join(os.path.dirname(__file__), "../../duofern.json")): str
            })
        )
