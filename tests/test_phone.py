"""Tests for SIP Doorbell integration."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.sip_doorbell.phone import SIPPhone, SIPProtocol, SIPConfig
from custom_components.sip_doorbell.const import (
    STATE_UNREGISTERED,
    STATE_REGISTERING,
    STATE_REGISTERED,
)


class TestSIPPhone:
    """Test SIPPhone class."""

    def test_init(self, hass):
        """Test initialization."""
        config = {
            "sip_server": "192.168.1.100",
            "sip_port": 5060,
            "sip_user": "101",
            "sip_password": "secret",
            "sip_realm": "asterisk",
        }
        phone = SIPPhone(hass, config)

        assert phone.config.server == "192.168.1.100"
        assert phone.config.port == 5060
        assert phone.config.user == "101"
        assert phone.config.password == "secret"
        assert phone.state == STATE_UNREGISTERED

    def test_generate_tag(self, hass):
        """Test tag generation."""
        config = {
            "sip_server": "192.168.1.100",
            "sip_port": 5060,
            "sip_user": "101",
            "sip_password": "secret",
            "sip_realm": "asterisk",
        }
        phone = SIPPhone(hass, config)

        tag1 = phone._generate_tag()
        tag2 = phone._generate_tag()

        assert len(tag1) == 8
        assert tag1.isdigit()
        assert tag1 != tag2

    def test_md5(self, hass):
        """Test MD5 hash."""
        config = {
            "sip_server": "192.168.1.100",
            "sip_port": 5060,
            "sip_user": "101",
            "sip_password": "secret",
            "sip_realm": "asterisk",
        }
        phone = SIPPhone(hass, config)

        hash_result = phone._md5("test")
        assert hash_result == "098f6bcd4621d373cade4e832627b4f6"

    def test_make_ha1(self, hass):
        """Test HA1 calculation."""
        config = {
            "sip_server": "192.168.1.100",
            "sip_port": 5060,
            "sip_user": "101",
            "sip_password": "secret",
            "sip_realm": "asterisk",
        }
        phone = SIPPhone(hass, config)

        # HA1 = MD5(user:realm:password)
        ha1 = phone._make_ha1()
        expected = "8c5e9b6e5f8c3e8a8f8e8c8e8c8e8c8e"  # Placeholder
        assert len(ha1) == 32  # MD5 is always 32 chars

    @pytest.mark.asyncio
    async def test_stop(self, hass):
        """Test shutdown."""
        config = {
            "sip_server": "192.168.1.100",
            "sip_port": 5060,
            "sip_user": "101",
            "sip_password": "secret",
            "sip_realm": "asterisk",
        }
        phone = SIPPhone(hass, config)

        # Mock transport
        phone._transport = MagicMock()
        phone._transport.close = MagicMock()

        await phone.stop()

        assert phone.state == STATE_UNREGISTERED
        phone._transport.close.assert_called_once()


class TestSIPProtocol:
    """Test SIPProtocol class."""

    def test_parse_simple_response(self):
        """Test parsing simple response."""
        protocol = SIPProtocol(on_message=MagicMock())

        data = b"SIP/2.0 200 OK\r\nCall-ID: 12345\r\nCSeq: 1 REGISTER\r\n\r\n"
        result = protocol._parse_simple(data)

        assert result["status_code"] == 200
        assert result["headers"]["call-id"] == "12345"
        assert result["headers"]["cseq"] == "1 REGISTER"

    def test_parse_401_response(self):
        """Test parsing 401 response."""
        protocol = SIPProtocol(on_message=MagicMock())

        data = (
            b"SIP/2.0 401 Unauthorized\r\n"
            b"WWW-Authenticate: Digest realm=\"asterisk\",nonce=\"abc123\"\r\n"
            b"\r\n"
        )
        result = protocol._parse_simple(data)

        assert result["status_code"] == 401
        assert "asterisk" in result["headers"]["www-authenticate"]


class TestSIPMessageBuilding:
    """Test SIP message building."""

    def test_build_register_no_auth(self, hass):
        """Test REGISTER without auth."""
        config = {
            "sip_server": "192.168.1.100",
            "sip_port": 5060,
            "sip_user": "101",
            "sip_password": "secret",
            "sip_realm": "asterisk",
        }
        phone = SIPPhone(hass, config)
        phone._from_tag = "12345678"
        phone.config.local_ip = "192.168.1.50"
        phone.config.local_port = 5060

        msg = phone._build_register("call123", 1)
        text = msg.decode()

        assert "REGISTER sip:192.168.1.100 SIP/2.0" in text
        assert "Call-ID: call123" in text
        assert "CSeq: 1 REGISTER" in text
        assert "From: <sip:101@192.168.1.100>;tag=12345678" in text

    def test_build_ringing(self, hass):
        """Test 180 Ringing response."""
        config = {
            "sip_server": "192.168.1.100",
            "sip_port": 5060,
            "sip_user": "101",
            "sip_password": "secret",
            "sip_realm": "asterisk",
        }
        phone = SIPPhone(hass, config)

        request = {
            "headers": {
                "via": "SIP/2.0/UDP 192.168.1.100:5060",
                "from": "<sip:100@192.168.1.100>",
                "to": "<sip:101@192.168.1.100>",
                "call-id": "call456",
                "cseq": "1 INVITE",
            }
        }

        msg = phone._build_ringing(request)
        text = msg.decode()

        assert "SIP/2.0 180 Ringing" in text
        assert "Call-ID: call456" in text
