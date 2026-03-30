"""SIP status sensor."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DOMAIN,
    SIGNAL_STATE_CHANGED,
    SIGNAL_INCOMING_CALL,
    STATE_UNREGISTERED,
    STATE_REGISTERING,
    STATE_REGISTERED,
    STATE_RINGING,
    STATE_IN_CALL,
    STATE_HANGUP,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensors."""
    phone = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([SIPStatusSensor(phone, config_entry)])


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up from YAML."""
    if discovery_info is None:
        return
    phone = hass.data[DOMAIN].get("yaml_phone")
    if phone:
        async_add_entities([SIPStatusSensor(phone, None)])


class SIPStatusSensor(SensorEntity):
    """SIP registration status."""
    
    _attr_icon = "mdi:phone-voip"
    _attr_should_poll = False
    
    def __init__(self, phone, config_entry):
        self._phone = phone
        self._config_entry = config_entry
        self._attr_unique_id = f"{phone.user}_status"
        self._attr_name = f"SIP {phone.user} Status"
        self._incoming_from = None
        
    @property
    def native_value(self):
        """Return state."""
        return self._phone.state
        
    @property
    def extra_state_attributes(self):
        """Return attributes."""
        return {
            "server": self._phone.config.server,
            "port": self._phone.config.port,
            "user": self._phone.config.user,
            "local_ip": self._phone.config.local_ip,
            "local_port": self._phone.config.local_port,
            "incoming_from": self._incoming_from,
        }
        
    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._phone.user)},
            "name": f"SIP {self._phone.user}",
            "manufacturer": "SIP Doorbell",
            "model": "SIP Client",
        }
        
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
        
    def _state_changed(self, new_state):
        """Handle state change."""
        if new_state == STATE_HANGUP:
            self._incoming_from = None
        self.async_write_ha_state()
        
    def _incoming_call(self, info):
        """Handle incoming call."""
        self._incoming_from = info.get("from")
        self.async_write_ha_state()
