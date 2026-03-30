"""Constants for SIP Doorbell integration."""

DOMAIN = "sip_doorbell"

# Config keys
CONF_NAME = "name"
CONF_SIP_SERVER = "sip_server"
CONF_SIP_PORT = "sip_port"
CONF_SIP_USER = "sip_user"
CONF_SIP_PASSWORD = "sip_password"
CONF_SIP_REALM = "sip_realm"
CONF_AUTO_ANSWER = "auto_answer"
CONF_DTMF_DIGIT = "dtmf_digit"

# Defaults
DEFAULT_PORT = 5060
DEFAULT_REALM = "asterisk"
DEFAULT_DTMF = "1"
DEFAULT_NAME = "SIP Doorbell"

# States
STATE_UNREGISTERED = "unregistered"
STATE_REGISTERING = "registering"
STATE_REGISTERED = "registered"
STATE_RINGING = "ringing"
STATE_IN_CALL = "in_call"
STATE_HANGUP = "hangup"

# Signals
SIGNAL_STATE_CHANGED = f"{DOMAIN}_state_changed"
SIGNAL_INCOMING_CALL = f"{DOMAIN}_incoming_call"
SIGNAL_CALL_ENDED = f"{DOMAIN}_call_ended"

# Services
SERVICE_ANSWER = "answer"
SERVICE_HANGUP = "hangup"
SERVICE_SEND_DTMF = "send_dtmf"
SERVICE_CALL = "call"
