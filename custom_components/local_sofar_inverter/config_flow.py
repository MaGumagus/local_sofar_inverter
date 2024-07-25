from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import selector
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME, CONF_HOST, CONF_ELEVATION, CONF_SCAN_INTERVAL
from .const import DOMAIN, DEFAULT_NAME, CONF_SERVER_URL, CONF_SERVER_USER, CONF_SERVER_PASS, DEFAULT_SCAN_INTERVAL, DEFAULT_MIN_ELEVATION

@config_entries.HANDLERS.register(DOMAIN)
class LocalSofarInverterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
#    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_confirm(self, user_input=None):
        """Handle a flow start."""
        errors = {}
        if user_input is not None:
            return await self.async_step_init(user_input=None)
        return self.async_show_form(
            step_id="confirm", 
            errors=errors
        )
    
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title=DEFAULT_NAME, data=user_input)
        if user_input is None:
            user_input = {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=DOMAIN): str,
                vol.Required(CONF_HOST, default=CONF_SERVER_URL): str,
                vol.Required(CONF_USERNAME, default=CONF_SERVER_USER): str,
                vol.Required(CONF_PASSWORD, default=CONF_SERVER_PASS): str,
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
                vol.Required(CONF_ELEVATION, default=DEFAULT_MIN_ELEVATION): int
            }),
            errors=errors
        )
