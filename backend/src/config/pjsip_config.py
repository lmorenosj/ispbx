"""
Configuration parameters for PJSIP
"""

# Parameters to include in extension configuration
EXTENSION_PARAMS = [
    'context',     # Dialplan context for incoming calls
    'callerid',    # Caller ID for the extension
    'username',    # Authentication username
    'password',    # Authentication password
    'max_contacts',# Maximum number of contacts
    'auth_type',   # Authentication type (e.g., userpass)
    'auth',        # Authentication object name
    'aors',        # Address of Record
    'disallow',    # Codecs to disallow
    'allow'        # Codecs to allow
]
