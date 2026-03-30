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
