# SIP Doorbell for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![Version](https://img.shields.io/github/v/release/Miromani4/SIP-Phone-for-HA)
![Downloads](https://img.shields.io/github/downloads/Miromani4/SIP-Phone-for-HA/total)

Pure Python SIP client integration for Home Assistant. Designed specifically for doorbell/intercom systems with DTMF control.

---

## 🚀 Quick Start

### Installation via HACS

1. Open HACS → Integrations
2. Click **⋮** → **Custom repositories**
3. Add repository: `https://github.com/Miromani4/SIP-Phone-for-HA`
4. Category: **Integration**
5. Click **Add**
6. Find and install **SIP Doorbell**
7. **Restart Home Assistant**

### Manual Installation

Copy `custom_components/sip_doorbell/` to your `config/custom_components/`.

---

## ⚙️ Configuration

### UI Configuration (Recommended)

1. **Settings** → **Devices & Services** → **Add Integration** → **SIP Doorbell**
2. Enter your SIP credentials:

| Field | Description | Example |
|-------|-------------|---------|
| Name | Friendly name | `Front Door` |
| SIP Server | IP/hostname of SIP server | `192.168.1.100` |
| SIP Port | SIP port (UDP) | `5060` |
| SIP Username | Extension number | `101` |
| SIP Password | SIP password | `secret123` |
| SIP Realm | Authentication realm | `asterisk` |
| Auto Answer | Auto-answer calls | `false` |

### YAML Configuration

```yaml
sip_doorbell:
  sip_server: 192.168.1.100
  sip_port: 5060
  sip_user: "101"
  sip_password: "secret123"
  sip_realm: "asterisk"
  auto_answer: false
```

---

## 📱 Entities

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.sip_101_status` | Sensor | Registration status |
| `switch.sip_101_call` | Switch | Call control (answer/hangup) |
| `media_player.sip_101_media` | Media Player | Audio playback & volume control |

### Status States

- `unregistered` — Not connected to SIP server
- `registering` — Attempting to register
- `registered` — Registered and ready
- `ringing` — Incoming call
- `in_call` — Active call
- `hangup` — Call ended

---

## 🔧 Services

### `sip_doorbell.answer`
Answer incoming call.

```yaml
service: sip_doorbell.answer
```

### `sip_doorbell.hangup`
Hangup current call.

```yaml
service: sip_doorbell.hangup
```

### `sip_doorbell.send_dtmf`
Send DTMF digits (for door opening, menu navigation, etc.).

```yaml
service: sip_doorbell.send_dtmf
data:
  digits: "1"
  duration: 250
target:
  entity_id: switch.sip_101_call
```

### `sip_doorbell.call`
Make outgoing call (not yet implemented).

```yaml
service: sip_doorbell.call
data:
  number: "102"
```

---


## 🎙️ Media Player (v1.2.0+)

SIP Doorbell создаёт сущность `media_player` для каждого аккаунта:

### Возможности
- Воспроизведение мелодий звонка
- Управление громкостью (0-100%)
- Автоматическая индикация входящих звонков
- Интеграция с автоматизациями

### Service Examples

```yaml
# Воспроизведение мелодии
service: media_player.play_media
target:
  entity_id: media_player.sip_101_media
data:
  media_content_id: "/local/sounds/doorbell.mp3"
  media_content_type: "audio/mp3"

# Управление громкостью
service: media_player.volume_set
target:
  entity_id: media_player.sip_101_media
data:
  volume_level: 0.7
```

---

## 🎨 Frontend: Call Popup Card

Automatically shows a popup when an incoming call is detected.

### Installation

1. Add to Dashboard Resources:
   - **Settings** → **Dashboards** → **⋮** → **Resources** → **Add Resource**
   - URL: `/hacsfiles/sip_doorbell/call_popup.js`
   - Type: **Module**

2. **Add WebRTC Support** (v1.2.0+):
   - **Settings** → **Dashboards** → **⋮** → **Resources** → **Add Resource**
   - URL: `/hacsfiles/sip_doorbell/webrtc-client.js`
   - Type: **Module**

3. Add card to your dashboard:

```yaml
type: custom:sip-doorbell-call-popup
title: 🔔 Doorbell
auto_open: true
auto_close: true
timeout: 30
webrtc_enabled: true  # Включить WebRTC аудио (v1.2.0+)
```

### Features

- ✅ Auto-open on incoming call
- ✅ Caller ID display (name & number)
- ✅ Answer/Hangup buttons
- ✅ DTMF keypad for door opening
- ✅ Auto-close after timeout
- ✅ **WebRTC двустороннее аудио** (v1.2.0+)
- ✅ **Кастомизация интерфейса** (v1.2.0+)

### 🎨 Кастомизация Popup (v1.2.0+)

Всплывающее окно можно настроить через Home Assistant themes:

```yaml
# configuration.yaml
frontend:
  themes:
    my_sip_theme:
      # Цвета
      sip-popup-primary-color: "#4CAF50"
      sip-popup-decline-color: "#F44336"
      
      # Размеры
      sip-popup-width: "450px"
      sip-popup-border-radius: "16px"
      
      # Анимация
      sip-popup-animation: "slideInRight"
      # Варианты: slideInRight, slideInLeft, fadeIn, bounceIn
```

### Advanced CSS Customization

```yaml
type: custom:mod-card
style: |
  sip-call-popup {
    --popup-bg-color: var(--card-background-color);
    --popup-border-radius: 20px;
    --popup-box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    --popup-title-size: 1.8em;
  }
card:
  type: custom:sip-doorbell-call-popup
  webrtc_enabled: true
```

---

## 🤖 Automation Examples

### Auto-open door on call

```yaml
alias: "Doorbell - Auto open door"
description: "Answer call, send DTMF 1 to open door, hangup"
trigger:
  - platform: state
    entity_id: sensor.sip_101_status
    to: "ringing"
condition: []
action:
  - service: switch.turn_on
    target:
      entity_id: switch.sip_101_call
    alias: "Answer call"
  
  - delay: "00:00:01"
  
  - service: sip_doorbell.send_dtmf
    data:
      digits: "1"
      duration: 300
    alias: "Send DTMF 1 to open door"
  
  - delay: "00:00:02"
  
  - service: switch.turn_off
    target:
      entity_id: switch.sip_101_call
    alias: "Hangup"
  
  - service: notify.mobile_app_phone
    data:
      message: "🔓 Door opened via intercom"
      title: "Doorbell"
```

### Send notification on incoming call

```yaml
alias: "Doorbell - Notify on call"
trigger:
  - platform: event
    event_type: sip_doorbell_incoming_call
action:
  - service: notify.mobile_app_phone
    data:
      title: "🔔 Doorbell Ringing"
      message: "Caller: {{ trigger.event.data.caller_name }} ({{ trigger.event.data.caller_number }})"
      data:
        tag: "doorbell_call"
```

### Video recording on doorbell press

```yaml
alias: "Doorbell - Start recording"
trigger:
  - platform: state
    entity_id: sensor.sip_101_status
    to: "ringing"
action:
  - service: camera.record
    target:
      entity_id: camera.front_door
    data:
      duration: 30
```

---


## 🌐 WebSocket API

For custom frontend integrations.

### Subscribe to call events

```javascript
const subscription = await hass.connection.subscribeMessage(
  (message) => {
    console.log('Call event:', message.event);
    // event_type: 'sip_doorbell_incoming_call' or 'sip_doorbell_call_ended'
    // data: { caller_name, caller_number, extension, timestamp }
  },
  { type: 'sip_doorbell/subscribe_calls' }
);
```

### Get phone status

```javascript
const status = await hass.callWS({
  type: 'sip_doorbell/get_status',
  extension: '101'
});
// Returns: { state, extension, server, local_ip, local_port }
```

### WebRTC Signaling (v1.2.0+)

```javascript
// Start WebRTC call
const result = await hass.callWS({
  type: 'sip_doorbell/webrtc_offer',
  extension: '101',
  sdp: offer.sdp,
  call_id: 'unique-call-id'
});
// Returns: { sdp: answer_sdp }

// Send ICE candidate
await hass.callWS({
  type: 'sip_doorbell/webrtc_ice_candidate',
  extension: '101',
  call_id: 'unique-call-id',
  candidate: iceCandidate
});

// Close WebRTC
await hass.callWS({
  type: 'sip_doorbell/webrtc_close',
  extension: '101',
  call_id: 'unique-call-id'
});
```

---

## 🐛 Troubleshooting

### Not registering

1. Check credentials in Asterisk/FreePBX
2. Verify network connectivity:
   ```bash
   nc -zv 192.168.1.100 5060
   ```
3. Check Asterisk CLI:
   ```bash
   asterisk -rvvv
   pjsip show registrations
   ```

### DTMF not working

Ensure Asterisk DTMF mode is set correctly:
```ini
dtmf_mode = rfc4733
; or
dtmf_mode = info
```

### Enable debug logging

```yaml
logger:
  logs:
    custom_components.sip_doorbell: debug
```

---

## 📋 Requirements

- Home Assistant 2023.1.0 or newer
- Python 3.10+
- SIP server (Asterisk, FreePBX, etc.)
- UDP port 5060 accessible from Home Assistant

---


## 📝 Changelog

### v1.2.0 (2026-03-31)
**Major Feature: WebRTC Audio & Customization**
- ✅ **WebRTC** - Нативное двустороннее аудио
- ✅ **Media Player** - Платформа для воспроизведения мелодий
- ✅ **Кастомизация Popup** - CSS переменные и темы
- ✅ **WebSocket API** - Команды для WebRTC сигналинга
- ✅ **JavaScript API** - Класс SIPWebRTCClient для разработчиков

### v1.1.0 (2026-03-30)
**Feature: Call Popup**
- ✅ WebSocket API for real-time call events
- ✅ Frontend popup card with auto-open
- ✅ Caller ID parsing from SIP headers
- ✅ DTMF panel in popup
- ✅ Auto-answer support

### v1.0.4 (2026-03-30)
**Fix: Thread-safe dispatch**
- ✅ Fixed asyncio.run_coroutine_threadsafe usage
- ✅ Resolved RuntimeError in async_dispatcher_send

### v1.0.3 (2026-03-30)
**Fix: Thread safety**
- ✅ Added @callback decorators
- ✅ Fixed STATE_* imports

### v1.0.2 (2026-03-30)
**Fix: Config flow**
- ✅ Added missing CONF_NAME constant

### v1.0.1 (2026-03-30)
**Fix: Minor bugfixes**

### v1.0.0 (2026-03-30)
**Initial Release**
- ✅ SIP registration without external libraries
- ✅ Incoming call detection
- ✅ Answer/Hangup control
- ✅ DTMF sending
- ✅ Multiple SIP accounts support

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- 🎵 RTP audio support (for two-way talk)
- 📹 Video support
- 📞 Outgoing call implementation
- 🔐 TLS transport support
- 📊 Better call history/logging

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Home Assistant team for the excellent framework
- Asterisk community for SIP documentation
- All contributors and testers

---

**Support:** Open an issue on [GitHub](https://github.com/Miromani4/SIP-Phone-for-HA/issues)
