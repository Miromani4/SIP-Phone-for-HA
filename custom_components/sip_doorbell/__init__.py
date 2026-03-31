"""SIP Doorbell integration for Home Assistant."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import websocket_api

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
    EVENT_INCOMING_CALL,
)

from .phone import SIPPhone

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.MEDIA_PLAYER]

# WebRTC peer connections storage
WEBRTC_PEERS = {}

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
    
    # Setup services and websocket
    _setup_services(hass, phone)
    _setup_websocket(hass)
    
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
    _setup_websocket(hass)
    
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


def _setup_websocket(hass: HomeAssistant) -> None:
    """Setup WebSocket API for call events and WebRTC signaling."""
    
    @websocket_api.websocket_command({
        vol.Required("type"): f"{DOMAIN}/subscribe_calls",
    })
    @websocket_api.async_response
    async def websocket_subscribe_calls(hass, connection, msg):
        """Subscribe to incoming call events."""
        
        def forward_event(event):
            """Forward HA event to WebSocket client."""
            connection.send_message({
                "id": msg["id"],
                "type": "event",
                "event": {
                    "event_type": event.event_type,
                    "data": event.data,
                    "time_fired": event.time_fired.isoformat(),
                },
            })
        
        # Subscribe to incoming call events
        cancel_listener = hass.bus.async_listen(
            EVENT_INCOMING_CALL, forward_event
        )
        
        # Store cleanup function
        connection.subscriptions[msg["id"]] = cancel_listener
        connection.send_message({"id": msg["id"], "type": "result", "success": True})
    
    @websocket_api.websocket_command({
        vol.Required("type"): f"{DOMAIN}/get_status",
        vol.Optional("extension"): str,
    })
    @websocket_api.async_response
    async def websocket_get_status(hass, connection, msg):
        """Get current SIP phone status."""
        extension = msg.get("extension")
        
        # Find phone by extension
        phone = None
        for key, obj in hass.data.get(DOMAIN, {}).items():
            if key == "yaml_phone":
                if not extension or obj.config.user == extension:
                    phone = obj
                    break
            elif hasattr(obj, 'config') and obj.config.user == extension:
                phone = obj
                break
        
        if phone:
            connection.send_result(msg["id"], {
                "state": phone.state,
                "extension": phone.config.user,
                "server": phone.config.server,
                "local_ip": phone.config.local_ip,
                "local_port": phone.config.local_port,
            })
        else:
            connection.send_error(msg["id"], "not_found", "Phone not found")
    
    # === WebRTC WebSocket Commands ===
    
    @websocket_api.websocket_command({
        vol.Required("type"): f"{DOMAIN}/webrtc_offer",
        vol.Required("extension"): str,
        vol.Required("sdp"): str,
        vol.Required("call_id"): str,
    })
    @websocket_api.async_response
    async def websocket_webrtc_offer(hass, connection, msg):
        """Handle WebRTC offer from client."""
        extension = msg["extension"]
        sdp = msg["sdp"]
        call_id = msg["call_id"]
        
        # Store peer connection info
        if extension not in WEBRTC_PEERS:
            WEBRTC_PEERS[extension] = {}
        
        WEBRTC_PEERS[extension][call_id] = {
            "connection": connection,
            "client_sdp": sdp,
        }
        
        # Find phone and set up media stream
        phone = None
        for key, obj in hass.data.get(DOMAIN, {}).items():
            if hasattr(obj, 'config') and obj.config.user == extension:
                phone = obj
                break
        
        if phone and hasattr(phone, 'handle_webrtc_offer'):
            answer_sdp = await phone.handle_webrtc_offer(sdp, call_id)
            connection.send_result(msg["id"], {
                "sdp": answer_sdp,
                "call_id": call_id,
            })
        else:
            connection.send_error(msg["id"], "webrtc_error", "WebRTC not supported or phone not found")
    
    @websocket_api.websocket_command({
        vol.Required("type"): f"{DOMAIN}/webrtc_ice_candidate",
        vol.Required("extension"): str,
        vol.Required("call_id"): str,
        vol.Required("candidate"): dict,
    })
    @websocket_api.async_response
    async def websocket_webrtc_ice(hass, connection, msg):
        """Handle ICE candidate from client."""
        extension = msg["extension"]
        call_id = msg["call_id"]
        candidate = msg["candidate"]
        
        phone = None
        for key, obj in hass.data.get(DOMAIN, {}).items():
            if hasattr(obj, 'config') and obj.config.user == extension:
                phone = obj
                break
        
        if phone and hasattr(phone, 'add_ice_candidate'):
            await phone.add_ice_candidate(call_id, candidate)
            connection.send_result(msg["id"], {"success": True})
        else:
            connection.send_error(msg["id"], "webrtc_error", "WebRTC not supported")
    
    @websocket_api.websocket_command({
        vol.Required("type"): f"{DOMAIN}/webrtc_close",
        vol.Required("extension"): str,
        vol.Required("call_id"): str,
    })
    @websocket_api.async_response
    async def websocket_webrtc_close(hass, connection, msg):
        """Close WebRTC connection."""
        extension = msg["extension"]
        call_id = msg["call_id"]
        
        # Clean up peer connection
        if extension in WEBRTC_PEERS and call_id in WEBRTC_PEERS[extension]:
            del WEBRTC_PEERS[extension][call_id]
        
        phone = None
        for key, obj in hass.data.get(DOMAIN, {}).items():
            if hasattr(obj, 'config') and obj.config.user == extension:
                phone = obj
                break
        
        if phone and hasattr(phone, 'close_webrtc'):
            await phone.close_webrtc(call_id)
        
        connection.send_result(msg["id"], {"success": True})
    
    # Register WebSocket commands
    websocket_api.async_register_command(hass, websocket_subscribe_calls)
    websocket_api.async_register_command(hass, websocket_get_status)
    websocket_api.async_register_command(hass, websocket_webrtc_offer)
    websocket_api.async_register_command(hass, websocket_webrtc_ice)
    websocket_api.async_register_command(hass, websocket_webrtc_close)


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
