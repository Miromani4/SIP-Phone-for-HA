# Configuration Guide

## Required Settings

| Setting | Type | Required | Description |
|---------|------|----------|-------------|
| `sip_server` | string | Yes | IP address or hostname of your SIP server (Asterisk/FreePBX) |
| `sip_user` | string | Yes | SIP extension number or username |
| `sip_password` | string | Yes | SIP password for authentication |

## Optional Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `sip_port` | integer | 5060 | SIP port (UDP) |
| `sip_realm` | string | "asterisk" | SIP realm/domain for authentication |
| `auto_answer` | boolean | false | Automatically answer incoming calls |

## YAML Configuration Example

```yaml
sip_doorbell:
  sip_server: 192.168.1.100
  sip_port: 5060
  sip_user: "101"
  sip_password: "mysecretpassword"
  sip_realm: "asterisk"
  auto_answer: false
```

## Multiple SIP Accounts

Configure multiple instances via UI:
1. Settings → Devices & Services → Add Integration → SIP Doorbell
2. Enter credentials for first account
3. Repeat for additional accounts

Each account creates separate entities:
- `sensor.sip_101_status`
- `sensor.sip_102_status`
- `switch.sip_101_call`
- `switch.sip_102_call`

## Network Requirements

- UDP port 5060 (or custom) must be accessible from Home Assistant to SIP server
- Home Assistant needs static IP for reliable registration
- Firewall rules may be needed if SIP server is on different subnet

## Call Popup Configuration

The SIP Doorbell integration includes a custom card for displaying incoming calls. The popup automatically appears when an incoming call is received.

### Adding the Card to Dashboard

1. Go to **Dashboard** → **Edit Dashboard**
2. Click **Manage Resources** (three dots menu)
3. Add new resource: `/config/custom_components/sip_doorbell/call_popup.js`
4. Click **Add Card** → **Manual**
5. Enter card type: `custom:sip-doorbell-call-popup`

### Card Configuration Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `title` | string | "🔔 Входящий звонок" | Popup title text |
| `auto_open` | boolean | true | Automatically open popup on incoming call |
| `auto_close` | boolean | false | Automatically close after timeout |
| `timeout` | integer | 30 | Auto-close timeout in seconds |
| `position` | string | "center" | Popup position: `center`, `top`, `bottom-right`, `bottom-left`, `top-right`, `top-left` |
| `theme` | string | "auto" | Theme: `light`, `dark`, `auto` (follows HA theme) |
| `camera_entity` | string | null | Camera entity to show video (e.g., `camera.doorbell`) |
| `enable_webrtc` | boolean | true | Enable WebRTC audio for calls |
| `show_audio_indicator` | boolean | true | Show audio activity indicator |
| `play_sound` | boolean | true | Play notification sound |
| `sound_url` | string | "/local/sounds/doorbell.mp3" | Path to notification sound file |

### Colors Configuration

```yaml
type: custom:sip-doorbell-call-popup
colors:
  answer: '#4caf50'      # Answer button color
  decline: '#f44336'    # Decline button color
  dtmf: '#2196f3'       # DTMF buttons color
  mute: '#ff9800'       # Mute button color
```

### Custom Actions

Add custom buttons to the popup (e.g., for door unlock):

```yaml
type: custom:sip-doorbell-call-popup
custom_actions:
  - name: "Unlock Door"
    icon: "mdi:lock-open"
    service: "lock.unlock"
    service_data:
      entity_id: lock.front_door
  - name: "Send *"
    dtmf_digit: "*"
    duration: 250
```

### Complete Configuration Example

```yaml
type: custom:sip-doorbell-call-popup
title: "🔔 Doorbell Ringing"
position: "bottom-right"
theme: "auto"
auto_open: true
auto_close: false
timeout: 30
width: "400px"
height: "auto"
camera_entity: camera.doorbell
enable_webrtc: true
show_audio_indicator: true
play_sound: true
sound_url: "/local/sounds/doorbell.mp3"
colors:
  answer: "#4caf50"
  decline: "#f44336"
  dtmf: "#2196f3"
  mute: "#ff9800"
custom_actions:
  - name: "Open Gate"
    icon: "mdi:gate-open"
    service: "switch.turn_on"
    service_data:
      entity_id: switch.gate_relay
```

### Hiding the Card

The popup card can be placed on any dashboard and will work even if hidden. To hide it:

```yaml
type: custom:sip-doorbell-call-popup
# Add to a hidden view or use card-mod to hide
style: |
  ha-card {
    display: none;
  }
```

> **Note:** The card must exist on some dashboard to receive WebSocket events and show the popup automatically.
