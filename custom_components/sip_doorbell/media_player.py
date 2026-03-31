"""SIP Media Player for audio notifications."""


from __future__ import annotations

import logging
import asyncio
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DOMAIN,
    SIGNAL_INCOMING_CALL,
    SIGNAL_CALL_ENDED,
    SIGNAL_STATE_CHANGED,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SIP media player."""
    phone = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([SIPMediaPlayer(phone, config_entry)])


class SIPMediaPlayer(MediaPlayerEntity):
    """SIP Media Player for ring sounds and notifications."""
    
    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
    )
    _attr_media_content_type = MediaType.MUSIC
    
    def __init__(self, phone, config_entry):
        """Initialize the media player."""
        self._phone = phone
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_media_player"
        self._attr_name = f"SIP {phone.config.user} Media"
        self._attr_device_class = "speaker"
        
        self._volume = 0.7
        self._is_playing = False
        self._media_title = None
        self._unsub_signals = []
        
    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the device."""
        if self._is_playing:
            return MediaPlayerState.PLAYING
        return MediaPlayerState.IDLE
        
    @property
    def volume_level(self) -> float:
        """Return the volume level."""
        return self._volume
        
    @property
    def media_title(self) -> str | None:
        """Return the title of current playing media."""
        return self._media_title
        
    async def async_added_to_hass(self) -> None:
        """Run when entity is added."""
        await super().async_added_to_hass()
        
        # Subscribe to signals
        self._unsub_signals.append(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_INCOMING_CALL,
                self._on_incoming_call
            )
        )
        self._unsub_signals.append(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_CALL_ENDED,
                self._on_call_ended
            )
        )
        
    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed."""
        await super().async_will_remove_from_hass()
        for unsub in self._unsub_signals:
            unsub()
            
    @callback
    def _on_incoming_call(self, data: dict) -> None:
        """Handle incoming call."""
        self._media_title = f"Incoming call from {data.get('caller_name', 'Unknown')}"
        self._is_playing = True
        self.async_write_ha_state()
        
    @callback
    def _on_call_ended(self, data: dict) -> None:
        """Handle call ended."""
        self._is_playing = False
        self._media_title = None
        self.async_write_ha_state()
        
    async def async_play_media(
        self, media_type: MediaType, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        if media_type != MediaType.MUSIC:
            _LOGGER.warning("Only music media type is supported")
            return
            
        self._media_title = media_id
        self._is_playing = True
        self.async_write_ha_state()
        
        # Fire event for frontend to play sound
        self.hass.bus.async_fire("sip_doorbell_play_sound", {
            "url": media_id,
            "volume": self._volume,
        })
        
    async def async_media_stop(self) -> None:
        """Send stop command."""
        self._is_playing = False
        self._media_title = None
        self.async_write_ha_state()
        
        self.hass.bus.async_fire("sip_doorbell_stop_sound")
        
    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level."""
        self._volume = max(0.0, min(1.0, volume))
        self.async_write_ha_state()