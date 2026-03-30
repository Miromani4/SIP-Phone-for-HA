"""Config flow for SIP Doorbell."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_SIP_SERVER,
    CONF_SIP_PORT,
    CONF_SIP_USER,
    CONF_SIP_PASSWORD,
    CONF_SIP_REALM,
    CONF_AUTO_ANSWER,
    DEFAULT_PORT,
    DEFAULT_REALM,
    DEFAULT_NAME,
)


class SipDoorbellConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle initial step."""
        errors = {}

        if user_input is not None:
            # Validate connection
            # TODO: Add connection test
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data=user_input
            )

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_SIP_SERVER): str,
                vol.Optional(CONF_SIP_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_SIP_USER): str,
                vol.Required(CONF_SIP_PASSWORD): str,
                vol.Optional(CONF_SIP_REALM, default=DEFAULT_REALM): str,
                vol.Optional(CONF_AUTO_ANSWER, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_AUTO_ANSWER,
                        default=self.config_entry.data.get(CONF_AUTO_ANSWER, False),
                    ): bool,
                }
            ),
        )
