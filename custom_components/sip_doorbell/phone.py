"""Pure asyncio SIP implementation."""
from __future__ import annotations

import logging
import asyncio
import hashlib
import random
import re
from dataclasses import dataclass
from typing import Optional, Callable, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    SIGNAL_STATE_CHANGED,
    SIGNAL_INCOMING_CALL,
    SIGNAL_CALL_ENDED,
    STATE_UNREGISTERED,
    STATE_REGISTERING,
    STATE_REGISTERED,
    STATE_RINGING,
    STATE_IN_CALL,
    STATE_HANGUP,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class SIPConfig:
    """SIP configuration."""
    server: str
    port: int
    user: str
    password: str
    realm: str
    local_ip: str = "0.0.0.0"
    local_port: int = 0


class SIPPhone:
    """Asyncio-based SIP phone."""
    
    def __init__(self, hass: HomeAssistant, config: dict):
        self.hass = hass
        self.config = SIPConfig(
            server=config["sip_server"],
            port=config.get("sip_port", 5060),
            user=config["sip_user"],
            password=config["sip_password"],
            realm=config.get("sip_realm", "asterisk"),
        )
        
        self._state = STATE_UNREGISTERED
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._protocol: Optional[SIPProtocol] = None
        self._register_task: Optional[asyncio.Task] = None
        self._call_task: Optional[asyncio.Task] = None
        self._cseq = 0
        self._call_id = None
        self._from_tag = None
        self._to_tag = None
        self._dialog = None
        self._pending_invite = None
        
    @property
    def state(self) -> str:
        """Current state."""
        return self._state
        
    @property
    def user(self) -> str:
        """SIP user."""
        return self.config.user
        
    def _set_state(self, new_state: str) -> None:
        """Update state and notify."""
        if self._state != new_state:
            _LOGGER.debug(f"State: {self._state} -> {new_state}")
            self._state = new_state
            async_dispatcher_send(self.hass, SIGNAL_STATE_CHANGED, new_state)
            
    def _generate_call_id(self) -> str:
        """Generate unique Call-ID."""
        return f"{random.randint(100000, 999999)}@{self.config.local_ip}"
        
    def _generate_tag(self) -> str:
        """Generate random tag."""
        return f"{random.randint(10000000, 99999999)}"
        
    def _md5(self, data: str) -> str:
        """Calculate MD5 hash."""
        return hashlib.md5(data.encode()).hexdigest()
        
    def _make_ha1(self) -> str:
        """Create HA1 for digest auth."""
        return self._md5(f"{self.config.user}:{self.config.realm}:{self.config.password}")
        
    def _make_response(self, method: str, uri: str, nonce: str) -> str:
        """Create authorization response."""
        ha1 = self._make_ha1()
        ha2 = self._md5(f"{method}:{uri}")
        return self._md5(f"{ha1}:{nonce}:{ha2}")
        
    def _build_register(self, call_id: str, cseq: int, auth: dict = None, expires: int = 3600) -> bytes:
        """Build REGISTER request."""
        from_uri = f"sip:{self.config.user}@{self.config.server}"
        to_uri = from_uri
        contact = f"sip:{self.config.user}@{self.config.local_ip}:{self.config.local_port}"
        
        headers = [
            f"REGISTER sip:{self.config.server} SIP/2.0",
            f"Via: SIP/2.0/UDP {self.config.local_ip}:{self.config.local_port};branch=z9hG4bK{cseq}",
            f"From: <{from_uri}>;tag={self._from_tag}",
            f"To: <{to_uri}>",
            f"Call-ID: {call_id}",
            f"CSeq: {cseq} REGISTER",
            f"Contact: <{contact}>",
            "Max-Forwards: 70",
            "User-Agent: SIP-Doorbell-HA/1.0",
            f"Expires: {expires}",
            "Content-Length: 0",
        ]
        
        if auth:
            response = self._make_response("REGISTER", from_uri, auth["nonce"])
            auth_header = (
                f'Digest username="{self.config.user}", '
                f'realm="{auth["realm"]}", '
                f'nonce="{auth["nonce"]}", '
                f'uri="{from_uri}", '
                f'response="{response}"'
            )
            headers.insert(4, f"Authorization: {auth_header}")
            
        return "\r\n".join(headers).encode() + b"\r\n\r\n"
        
    def _build_ack(self, request: dict) -> bytes:
        """Build ACK request."""
        headers = [
            f"ACK {request['uri']} SIP/2.0",
            f"Via: SIP/2.0/UDP {self.config.local_ip}:{self.config.local_port};branch={request['branch']}",
            f"From: {request['from']}",
            f"To: {request['to']}",
            f"Call-ID: {request['call_id']}",
            f"CSeq: {request['cseq']} ACK",
            "Content-Length: 0",
        ]
        return "\r\n".join(headers).encode() + b"\r\n\r\n"
        
    def _build_ok(self, request: dict) -> bytes:
        """Build 200 OK response."""
        headers = [
            "SIP/2.0 200 OK",
            f"Via: {request['via']}",
            f"From: {request['from']}",
            f"To: {request['to']};tag={self._generate_tag()}",
            f"Call-ID: {request['call_id']}",
            f"CSeq: {request['cseq']} {request['method']}",
            "Content-Length: 0",
        ]
        return "\r\n".join(headers).encode() + b"\r\n\r\n"
        
    def _build_bye(self, dialog: dict) -> bytes:
        """Build BYE request."""
        self._cseq += 1
        headers = [
            f"BYE {dialog['uri']} SIP/2.0",
            f"Via: SIP/2.0/UDP {self.config.local_ip}:{self.config.local_port};branch=z9hG4bK{self._cseq}",
            f"From: {dialog['from']}",
            f"To: {dialog['to']}",
            f"Call-ID: {dialog['call_id']}",
            f"CSeq: {self._cseq} BYE",
            "Content-Length: 0",
        ]
        return "\r\n".join(headers).encode() + b"\r\n\r\n"
        
    def _build_info_dtmf(self, dialog: dict, digit: str, duration: int) -> bytes:
        """Build INFO with DTMF."""
        self._cseq += 1
        body = f"Signal={digit}\r\nDuration={duration}"
        headers = [
            f"INFO {dialog['uri']} SIP/2.0",
            f"Via: SIP/2.0/UDP {self.config.local_ip}:{self.config.local_port};branch=z9hG4bK{self._cseq}",
            f"From: {dialog['from']}",
            f"To: {dialog['to']}",
            f"Call-ID: {dialog['call_id']}",
            f"CSeq: {self._cseq} INFO",
            "Content-Type: application/dtmf-relay",
            f"Content-Length: {len(body)}",
            "",
            body,
        ]
        return "\r\n".join(headers).encode() + b"\r\n"
        
    def _parse_message(self, data: bytes) -> dict:
        """Parse SIP message."""
        text = data.decode('utf-8', errors='ignore')
        lines = text.split('\r\n')
        
        if not lines:
            return {}
            
        result: dict[str, Any] = {"headers": {}, "body": ""}
        
        # First line
        first = lines[0]
        if first.startswith("SIP/2.0"):
            # Response
            match = re.match(r"SIP/2.0 (\d+) (.*)", first)
            if match:
                result["status_code"] = int(match.group(1))
                result["reason"] = match.group(2)
        else:
            # Request
            parts = first.split()
            if len(parts) >= 3:
                result["method"] = parts[0]
                result["uri"] = parts[1]
                
        # Headers
        i = 1
        while i < len(lines) and lines[i]:
            if ':' in lines[i]:
                key, value = lines[i].split(':', 1)
                result["headers"][key.strip().lower()] = value.strip()
            i += 1
            
        # Body
        if i < len(lines):
            result["body"] = '\r\n'.join(lines[i+1:])
            
        return result
        
    async def start(self) -> None:
        """Start SIP phone."""
        try:
            self._set_state(STATE_REGISTERING)
            
            # Create UDP socket
            loop = asyncio.get_event_loop()
            self._transport, self._protocol = await loop.create_datagram_endpoint(
                lambda: SIPProtocol(self._on_message),
                local_addr=(self.config.local_ip, self.config.local_port),
            )
            
            # Get actual local port
            sock = self._transport.get_extra_info('socket')
            self.config.local_port = sock.getsockname()[1]
            self.config.local_ip = sock.getsockname()[0]
            
            _LOGGER.info(f"SIP socket bound to {self.config.local_ip}:{self.config.local_port}")
            
            # Generate tags
            self._from_tag = self._generate_tag()
            self._call_id = self._generate_call_id()
            
            # Start registration loop
            self._register_task = asyncio.create_task(self._register_loop())
            
        except Exception as e:
            _LOGGER.error(f"Failed to start: {e}")
            self._set_state(STATE_UNREGISTERED)
            
    async def _register_loop(self) -> None:
        """Registration loop with re-registration."""
        retry_delay = 30
        
        while True:
            try:
                if await self._do_register():
                    # Success, re-register after 300s
                    await asyncio.sleep(300)
                else:
                    # Failed, retry
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 300)
            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOGGER.error(f"Registration error: {e}")
                await asyncio.sleep(retry_delay)
                
    async def _do_register(self) -> bool:
        """Perform single registration."""
        self._cseq += 1
        
        # First attempt without auth
        msg = self._build_register(self._call_id, self._cseq)
        self._transport.sendto(msg, (self.config.server, self.config.port))
        
        # Wait response
        try:
            response = await asyncio.wait_for(
                self._protocol.wait_for_response(self._call_id, self._cseq),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            _LOGGER.warning("Registration timeout")
            return False
            
        if response.get("status_code") == 200:
            _LOGGER.info("Registered successfully")
            self._set_state(STATE_REGISTERED)
            return True
            
        elif response.get("status_code") == 401:
            # Need auth
            www_auth = response["headers"].get("www-authenticate", "")
            match = re.search(r'nonce="([^"]+)"', www_auth)
            if not match:
                _LOGGER.error("No nonce in 401 response")
                return False
                
            nonce = match.group(1)
            realm_match = re.search(r'realm="([^"]+)"', www_auth)
            realm = realm_match.group(1) if realm_match else self.config.realm
            
            # Second attempt with auth
            self._cseq += 1
            auth = {"nonce": nonce, "realm": realm}
            msg = self._build_register(self._call_id, self._cseq, auth)
            self._transport.sendto(msg, (self.config.server, self.config.port))
            
            try:
                response = await asyncio.wait_for(
                    self._protocol.wait_for_response(self._call_id, self._cseq),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                _LOGGER.warning("Auth registration timeout")
                return False
                
            if response.get("status_code") == 200:
                _LOGGER.info("Registered with auth")
                self._set_state(STATE_REGISTERED)
                return True
            else:
                _LOGGER.error(f"Auth failed: {response.get('status_code')}")
                return False
        else:
            _LOGGER.error(f"Registration failed: {response.get('status_code')}")
            return False
            
    def _on_message(self, data: bytes, addr: tuple) -> None:
        """Handle incoming SIP message."""
        msg = self._parse_message(data)
        
        if "method" in msg:
            # Request
            if msg["method"] == "INVITE":
                asyncio.create_task(self._handle_invite(msg, addr))
            elif msg["method"] == "BYE":
                asyncio.create_task(self._handle_bye(msg))
            elif msg["method"] == "ACK":
                pass  # Ignore
            elif msg["method"] == "CANCEL":
                asyncio.create_task(self._handle_cancel(msg))
        else:
            # Response - handled by protocol
            self._protocol.handle_response(msg)
            
    async def _handle_invite(self, msg: dict, addr: tuple) -> None:
        """Handle incoming INVITE."""
        _LOGGER.info(f"Incoming call from {msg['headers'].get('from', 'Unknown')}")
        
        # Save dialog info
        self._dialog = {
            "uri": msg["uri"],
            "from": msg["headers"].get("from"),
            "to": msg["headers"].get("to"),
            "call_id": msg["headers"].get("call-id"),
            "via": msg["headers"].get("via"),
            "cseq": msg["headers"].get("cseq", "0").split()[0],
            "branch": self._extract_branch(msg["headers"].get("via", "")),
            "remote_addr": addr,
        }
        
        # Send 180 Ringing
        ringing = self._build_ringing(msg)
        self._transport.sendto(ringing, addr)
        
        self._set_state(STATE_RINGING)
        self._pending_invite = msg
        
        # Notify HA
        async_dispatcher_send(self.hass, SIGNAL_INCOMING_CALL, {
            "from": msg["headers"].get("from"),
            "to": msg["headers"].get("to"),
        })
        
    def _build_ringing(self, request: dict) -> bytes:
        """Build 180 Ringing response."""
        headers = [
            "SIP/2.0 180 Ringing",
            f"Via: {request['headers'].get('via')}",
            f"From: {request['headers'].get('from')}",
            f"To: {request['headers'].get('to')};tag={self._generate_tag()}",
            f"Call-ID: {request['headers'].get('call-id')}",
            f"CSeq: {request['headers'].get('cseq')} INVITE",
            "Content-Length: 0",
        ]
        return "\r\n".join(headers).encode() + b"\r\n\r\n"
        
    async def _handle_bye(self, msg: dict) -> None:
        """Handle BYE."""
        _LOGGER.info("Remote hung up")
        self._set_state(STATE_HANGUP)
        async_dispatcher_send(self.hass, SIGNAL_CALL_ENDED, {})
        
        # Send 200 OK
        ok = self._build_ok(msg)
        self._transport.sendto(ok, self._dialog["remote_addr"] if self._dialog else None)
        
        await asyncio.sleep(1)
        self._set_state(STATE_REGISTERED)
        
    async def _handle_cancel(self, msg: dict) -> None:
        """Handle CANCEL."""
        _LOGGER.info("Call cancelled")
        self._set_state(STATE_REGISTERED)
        
        # Send 200 OK for CANCEL and 487 for INVITE
        ok = self._build_ok(msg)
        self._transport.sendto(ok)
        
    def _extract_branch(self, via: str) -> str:
        """Extract branch from Via header."""
        match = re.search(r'branch=([^;]+)', via)
        return match.group(1) if match else ""
        
    async def answer(self) -> None:
        """Answer incoming call."""
        if not self._pending_invite:
            _LOGGER.warning("No incoming call to answer")
            return
            
        _LOGGER.info("Answering call")
        
        # Build 200 OK with SDP (simplified)
        sdp = self._build_sdp()
        ok = self._build_ok_with_sdp(self._pending_invite, sdp)
        
        self._transport.sendto(ok, self._dialog["remote_addr"])
        self._set_state(STATE_IN_CALL)
        
        # Wait for ACK
        # In real implementation, need proper dialog management
        
    def _build_sdp(self) -> str:
        """Build minimal SDP."""
        return (
            "v=0\r\n"
            f"o=- {random.randint(1000,9999)} {random.randint(1000,9999)} IN IP4 {self.config.local_ip}\r\n"
            "s=SIP Doorbell\r\n"
            f"c=IN IP4 {self.config.local_ip}\r\n"
            "t=0 0\r\n"
            "m=audio 0 RTP/AVP 0\r\n"  # 0 = PCMU
            "a=rtpmap:0 PCMU/8000\r\n"
        )
        
    def _build_ok_with_sdp(self, request: dict, sdp: str) -> bytes:
        """Build 200 OK with SDP."""
        to_tag = self._generate_tag()
        self._to_tag = to_tag
        
        headers = [
            "SIP/2.0 200 OK",
            f"Via: {request['headers'].get('via')}",
            f"From: {request['headers'].get('from')}",
            f"To: {request['headers'].get('to')};tag={to_tag}",
            f"Call-ID: {request['headers'].get('call-id')}",
            f"CSeq: {request['headers'].get('cseq')} INVITE",
            "Content-Type: application/sdp",
            f"Content-Length: {len(sdp)}",
            "",
            sdp,
        ]
        return "\r\n".join(headers).encode() + b"\r\n"
        
    async def hangup(self) -> None:
        """Hangup call."""
        if self._state == STATE_IN_CALL and self._dialog:
            _LOGGER.info("Hanging up")
            bye = self._build_bye(self._dialog)
            self._transport.sendto(bye, self._dialog["remote_addr"])
            
        self._set_state(STATE_HANGUP)
        await asyncio.sleep(1)
        self._set_state(STATE_REGISTERED)
        
    async def send_dtmf(self, digits: str, duration: int = 250) -> None:
        """Send DTMF via INFO."""
        if self._state != STATE_IN_CALL or not self._dialog:
            _LOGGER.warning("Cannot send DTMF: not in call")
            return
            
        for digit in digits:
            _LOGGER.info(f"Sending DTMF: {digit}")
            info = self._build_info_dtmf(self._dialog, digit, duration)
            self._transport.sendto(info, self._dialog["remote_addr"])
            await asyncio.sleep(0.1)
            
    async def call(self, number: str) -> None:
        """Make outgoing call."""
        _LOGGER.info(f"Calling {number}")
        # TODO: Implement outgoing INVITE
        pass
        
    async def stop(self) -> None:
        """Shutdown."""
        _LOGGER.info("Stopping SIP phone")
        
        if self._register_task:
            self._register_task.cancel()
            try:
                await self._register_task
            except asyncio.CancelledError:
                pass
                
        if self._transport:
            # Unregister
            if self._state == STATE_REGISTERED:
                self._cseq += 1
                msg = self._build_register(self._call_id, self._cseq, expires=0)
                self._transport.sendto(msg, (self.config.server, self.config.port))
                
            self._transport.close()
            
        self._set_state(STATE_UNREGISTERED)


class SIPProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler."""
    
    def __init__(self, on_message: Callable):
        self.on_message = on_message
        self._responses: dict[tuple, asyncio.Future] = {}
        
    def connection_made(self, transport):
        self.transport = transport
        
    def datagram_received(self, data, addr):
        """Handle incoming datagram."""
        # Check if it's a response we're waiting for
        msg = self._parse_simple(data)
        
        if "status_code" in msg:
            # Response
            call_id = msg.get("headers", {}).get("call-id")
            cseq = msg.get("headers", {}).get("cseq", "").split()[0]
            key = (call_id, int(cseq) if cseq else 0)
            
            if key in self._responses:
                self._responses[key].set_result(msg)
                del self._responses[key]
                return
                
        # Pass to handler
        self.on_message(data, addr)
        
    def _parse_simple(self, data: bytes) -> dict:
        """Simple parse for response detection."""
        text = data.decode('utf-8', errors='ignore')
        lines = text.split('\r\n')
        result: dict[str, Any] = {"headers": {}}
        
        if lines and lines[0].startswith("SIP/2.0"):
            parts = lines[0].split()
            if len(parts) >= 2:
                try:
                    result["status_code"] = int(parts[1])
                except ValueError:
                    pass
                    
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                result["headers"][key.strip().lower()] = value.strip()
                
        return result
        
    def error_received(self, exc):
        _LOGGER.error(f"Protocol error: {exc}")
        
    def connection_lost(self, exc):
        _LOGGER.warning("Connection lost")
        
    async def wait_for_response(self, call_id: str, cseq: int, timeout: float = 5.0):
        """Wait for specific response."""
        key = (call_id, cseq)
        future = asyncio.get_event_loop().create_future()
        self._responses[key] = future
        
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            if key in self._responses:
                del self._responses[key]
            raise
            
    def handle_response(self, msg: dict):
        """Handle response for matching."""
        pass
