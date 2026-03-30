"""SIP Doorbell integration for Home Assistant."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

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
    SERVICE_ANSWER,
    SERVICE_HANGUP,
    SERVICE_SEND_DTMF,
    SERVICE_CALL,
)

from .phone import SIPPhone

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.SWITCH]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_SIP_SERVER): str,
                vol.Optional(CONF_SIP_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_SIP_USER): str,
                vol.Required(CONF_SIP_PASSWORD): str,
                vol.Optional(CONF_SIP_REALM, default=DEFAULT_REALM): str,
                vol.Optional(CONF_AUTO_ANSWER, default=False): bool,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up from YAML."""
    hass.data.setdefault(DOMAIN, {})
    
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    
    # Create phone instance
    phone = SIPPhone(hass, conf)
    hass.data[DOMAIN]["yaml_phone"] = phone
    
    # Start registration
    hass.async_create_background_task(phone.start(), "sip_start")
    
    # Setup services
    _setup_services(hass, phone)
    
    # Forward to platforms
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform("sensor", DOMAIN, {}, config)
    )
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform("switch", DOMAIN, {}, config)
    )
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from config entry (UI)."""
    hass.data.setdefault(DOMAIN, {})
    
    phone = SIPPhone(hass, entry.data)
    hass.data[DOMAIN][entry.entry_id] = phone
    
    hass.async_create_background_task(phone.start(), "sip_start")
    _setup_services(hass, phone)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


def _setup_services(hass: HomeAssistant, phone: SIPPhone) -> None:
    """Register services."""
    
    async def async_answer(call):
        """Answer incoming call."""
        await phone.answer()
        
    async def async_hangup(call):
        """Hangup call."""
        await phone.hangup()
        
    async def async_send_dtmf(call):
        """Send DTMF digits."""
        digits = call.data.get("digits", "1")
        duration = call.data.get("duration", 250)
        await phone.send_dtmf(digits, duration)
        
    async def async_call(call):
        """Make outgoing call."""
        number = call.data.get("number")
        if number:
            await phone.call(number)

    hass.services.async_register(DOMAIN, SERVICE_ANSWER, async_answer)
    hass.services.async_register(DOMAIN, SERVICE_HANGUP, async_hangup)
    hass.services.async_register(DOMAIN, SERVICE_SEND_DTMF, async_send_dtmf)
    hass.services.async_register(DOMAIN, SERVICE_CALL, async_call)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload."""
    phone = hass.data[DOMAIN].pop(entry.entry_id, None)
    if phone:
        await phone.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
