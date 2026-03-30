# SIP Doorbell for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Pure Python SIP client integration for Home Assistant. Designed specifically for doorbell/intercom systems with DTMF control.

## Why?

- Existing solutions require AMI access or Docker containers
- This works with **just SIP credentials** — no server access needed
- Zero external dependencies (pure asyncio)
- Lightweight — runs within HA process

## Installation

### HACS (recommended)

1. Go to HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/your-username/sip-doorbell-ha`
3. Install **SIP Doorbell**
4. Restart Home Assistant

### Manual

Copy `custom_components/sip_doorbell/` to your `config/custom_components/`.

## Configuration

### UI (recommended)

Settings → Devices & Services → Add Integration → SIP Doorbell

### YAML

```yaml
sip_doorbell:
  sip_server: 192.168.15.151      # Your Asterisk/FreePBX IP
  sip_port: 5060                   # SIP port (usually 5060)
  sip_user: "101"                  # Extension number
  sip_password: "secret"           # SIP password
  sip_realm: "asterisk"            # Realm (usually "asterisk")
  auto_answer: false               # Auto-answer incoming calls
```

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.sip_XXX_status` | Sensor | Registration status: unregistered/registering/registered/ringing/in_call |
| `switch.sip_XXX_call` | Switch | Call control: ON = answer/in call, OFF = hangup |

## Services

| Service | Description |
|---------|-------------|
| `sip_doorbell.answer` | Answer incoming call |
| `sip_doorbell.hangup` | Hangup current call |
| `sip_doorbell.send_dtmf` | Send DTMF digits (e.g., "1" to open door) |
| `sip_doorbell.call` | Make outgoing call |

## Automation Example

```yaml
alias: "Doorbell - Auto open"
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
    alias: "Answer"
  
  - delay: "00:00:01"
  
  - service: sip_doorbell.send_dtmf
    data:
      digits: "1"
      duration: 300
  
  - delay: "00:00:02"
  
  - service: switch.turn_off
    target:
      entity_id: switch.sip_101_call
    alias: "Hangup"
  
  - service: notify.mobile_app_phone
    data:
      message: "🔓 Door opened via intercom"
```

## Dashboard Card

```yaml
type: conditional
conditions:
  - entity: sensor.sip_101_status
    state: "ringing"
card:
  type: alarm-panel
  name: 🔔 Doorbell ringing
  states:
    - arm_home
  buttons:
    - name: Open door
      service: script.open_door_dtmf
      icon: mdi:door-open
```

## Troubleshooting

### Not registering

Check in Asterisk CLI:
```bash
pjsip show registrations
pjsip show endpoints
```

### No audio/DTMF not working

Ensure your Asterisk supports:
- DTMF mode: `rfc4733` or `info`
- Codec: `PCMU` (μ-law)

## Architecture

```
┌─────────────┐     UDP/SIP      ┌─────────────┐
│  Home       │ ◄──────────────► │  Asterisk   │
│  Assistant  │   REGISTER       │  192.168... │
│             │   INVITE/200 OK  │             │
│  sip_doorbell│ ◄──────────────► │  Doorbell   │
│  (asyncio)   │   DTMF (INFO)    │  Extension  │
└─────────────┘                  └─────────────┘
```

## Contributing

PRs welcome! Focus areas:
- RTP audio support
- Video support
- Multiple concurrent calls
- TLS transport

## License

MIT
