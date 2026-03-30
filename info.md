# SIP Doorbell

Pure Python SIP client for Home Assistant. No external dependencies, no Docker containers.

## ✨ Features

- ✅ SIP registration without external libraries
- ✅ Incoming call detection with Caller ID
- ✅ Answer/Hangup control via switch entity
- ✅ DTMF sending (for door opening)
- ✅ Auto-answer option
- ✅ Multiple SIP accounts support
- ✅ WebSocket API for custom frontends
- ✅ Auto-open popup card on incoming calls
- ✅ Works with any SIP server (Asterisk, FreePBX, etc.)

## 📦 Installation

1. Add to HACS as custom repository
2. Install "SIP Doorbell"
3. **Restart Home Assistant**
4. Configure via UI or YAML

## ⚙️ Configuration

### YAML Example

```yaml
sip_doorbell:
  sip_server: 192.168.1.100
  sip_port: 5060
  sip_user: "101"
  sip_password: "secret"
  sip_realm: "asterisk"
  auto_answer: false
```

### UI Configuration

Settings → Devices & Services → Add Integration → SIP Doorbell

## 🎨 Call Popup Card

Automatically shows a popup when someone rings the doorbell.

### Add to Dashboard

1. Settings → Dashboards → Resources → Add Resource
2. URL: `/hacsfiles/sip_doorbell/call_popup.js`
3. Type: Module

### Card Configuration

```yaml
type: custom:sip-doorbell-call-popup
title: 🔔 Doorbell
auto_open: true
auto_close: true
timeout: 30
```

## 🤖 Automation Example

```yaml
alias: "Open door on call"
trigger:
  - platform: state
    entity_id: sensor.sip_101_status
    to: "ringing"
action:
  - service: switch.turn_on
    target:
      entity_id: switch.sip_101_call
  - delay: 1
  - service: sip_doorbell.send_dtmf
    data:
      digits: "1"
      duration: 300
  - delay: 2
  - service: switch.turn_off
    target:
      entity_id: switch.sip_101_call
```

## 📚 Documentation

- [Configuration Guide](docs/CONFIGURATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## 📝 Changelog

### v1.1.0
- WebSocket API for call events
- Frontend popup card
- Caller ID parsing

### v1.0.4
- Thread-safe dispatch fix

### v1.0.0
- Initial release

## 📄 License

MIT
