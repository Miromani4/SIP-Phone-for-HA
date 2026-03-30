# Troubleshooting Guide

## Common Issues

### 1. Not Registering

**Symptoms:** Sensor shows `unregistered` or `registering` state

**Solutions:**

1. **Check credentials:**
   - Verify SIP username/password in Asterisk
   - Check realm matches server configuration

2. **Network connectivity:**
   ```bash
   # From Home Assistant host
   nc -zv 192.168.1.100 5060
   ```

3. **Asterisk CLI:**
   ```bash
   asterisk -rvvv
   pjsip show registrations
   pjsip show endpoints
   ```

4. **Check logs:**
   ```yaml
   logger:
     logs:
       custom_components.sip_doorbell: debug
   ```

### 2. Registration Timeout

**Symptoms:** "Registration timeout" in logs

**Solutions:**
- Ensure SIP server is reachable
- Check firewall rules
- Verify correct port (default 5060)
- Check if server requires TCP instead of UDP (not supported yet)

### 3. Auth Failed (401/403)

**Symptoms:** "Auth failed: 401" or "Auth failed: 403"

**Solutions:**
1. Verify password is correct
2. Check realm matches server configuration
3. In Asterisk (`pjsip.conf` or FreePBX):
   ```
   auth_realm = asterisk
   ```

### 4. Incoming Calls Not Detected

**Symptoms:** Calls come but sensor stays `registered`

**Solutions:**
- Check Asterisk outbound route sends INVITE correctly
- Verify extension is not set to "Do Not Disturb"
- Check if server requires TCP (current limitation)

### 5. DTMF Not Working

**Symptoms:** Door doesn't open when sending DTMF

**Solutions:**
1. **Asterisk DTMF mode:**
   ```
   dtmf_mode = rfc4733
   ; or
   dtmf_mode = info
   ```

2. **Try different duration:**
   ```yaml
   service: sip_doorbell.send_dtmf
   data:
     digits: "1"
     duration: 500  # Try longer duration
   ```

3. **Check Asterisk logs:**
   ```bash
   asterisk -rvvv
   core set verbose 5
   ```

### 5. One-Way Audio

**Note:** Current version doesn't support RTP audio. This is planned for future release.

## Debug Mode

Enable detailed logging:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.sip_doorbell: debug
    custom_components.sip_doorbell.phone: debug
```

Restart Home Assistant and check logs at:
- Settings → System → Logs
- Or `/config/home-assistant.log`

## Known Limitations

| Limitation | Status | Workaround |
|------------|--------|------------|
| No RTP audio | Planned | Use separate intercom app for audio |
| UDP only | Current | Most servers support UDP |
| No video | Planned | Use camera integration separately |
| Single call at a time | Current | Sufficient for doorbell use case |

## Getting Help

1. Check existing issues: https://github.com/your-username/sip-doorbell-ha/issues
2. Create new issue with:
   - Home Assistant version
   - SIP server type (Asterisk/FreePBX/other)
   - Debug logs
   - Network topology description
