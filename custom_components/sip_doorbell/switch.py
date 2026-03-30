"""SIP call control switch."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.core import callback

from .const import (
    DOMAIN,
    SIGNAL_STATE_CHANGED,
    SIGNAL_INCOMING_CALL,
    SIGNAL_CALL_ENDED,
    STATE_REGISTERED,
    STATE_RINGING,
    STATE_IN_CALL,
    STATE_HANGUP,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up switches."""
    phone = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([SIPCallSwitch(phone, config_entry)])


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up from YAML."""
    if discovery_info is None:
        return
    phone = hass.data[DOMAIN].get("yaml_phone")
    if phone:
        async_add_entities([SIPCallSwitch(phone, None)])


class SIPCallSwitch(SwitchEntity):
    """Control SIP call."""
    
    _attr_icon = "mdi:phone"
    _attr_should_poll = False
    
    def __init__(self, phone, config_entry):
        self._phone = phone
        self._config_entry = config_entry
        self._attr_unique_id = f"{phone.user}_call"
        self._attr_name = f"SIP {phone.user} Call"
        self._incoming_from = None
        
    @property
    def is_on(self):
        """True when in call."""
        return self._phone.state == STATE_IN_CALL
        
    @property
    def available(self):
        """Available when registered or in call."""
        return self._phone.state in [STATE_REGISTERED, STATE_RINGING, STATE_IN_CALL, STATE_HANGUP]
        
    @property
    def extra_state_attributes(self):
        """Return attributes."""
        return {
            "sip_state": self._phone.state,
            "incoming_from": self._incoming_from,
        }
        
    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._phone.user)},
            "name": f"SIP {phone.user}",
            "manufacturer": "SIP Doorbell",
            "model": "SIP Client",
        }
        
    async def async_turn_on(self, **kwargs):
        """Answer call."""
        await self._phone.answer()
        
    async def async_turn_off(self, **kwargs):
        """Hangup call."""
        await self._phone.hangup()
        
    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_STATE_CHANGED,
                self._state_changed
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_INCOMING_CALL,
                self._incoming_call
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_CALL_ENDED,
                self._call_ended
            )
        )
        
    @callback
    def _state_changed(self, new_state):
        """Handle state change."""
        _LOGGER.debug(f"Switch state changed: {new_state}")
        if new_state == STATE_HANGUP:
            self._incoming_from = None
        self.async_write_ha_state()
        
    @callback
    def _incoming_call(self, info):
        """Handle incoming call."""
        self._incoming_from = info.get("from")
        self.async_write_ha_state()
        
    @callback
    def _call_ended(self, info):
        """Handle call end."""
        self._incoming_from = None
        self.async_write_ha_state()
