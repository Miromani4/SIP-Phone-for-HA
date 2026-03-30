# SIP Doorbell

Pure Python SIP client for Home Assistant. No external dependencies, no Docker containers.

## Features

- ✅ SIP registration without external libraries
- ✅ Incoming call detection
- ✅ Answer/Hangup control
- ✅ DTMF sending (for door opening)
- ✅ Auto-answer option
- ✅ Multiple SIP accounts
- ✅ Works with any external Asterisk/FreePBX

## Installation

1. Add to HACS as custom repository
2. Install "SIP Doorbell"
3. Configure via UI or YAML

## Configuration

```yaml
sip_doorbell:
  sip_server: 192.168.15.151
  sip_port: 5060
  sip_user: "101"
  sip_password: "secret"
  auto_answer: false
```

## Usage

Automation example:
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
  - delay: 2
  - service: switch.turn_off
    target:
      entity_id: switch.sip_101_call
```
