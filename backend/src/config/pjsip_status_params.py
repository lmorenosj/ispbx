"""
Configuration file for PJSIP status parameters to be included in the response
"""

# Parameters to be included in the response for each event type
EVENT_FILTERS = {
    'EndpointDetail': {
        'type': 'ObjectType',
        'name': 'ObjectName',
        'device_state': 'DeviceState',
        'context': 'Context'
    },
    'AuthDetail': {
        'username': 'Username',
        'auth_type': 'AuthType'
    },
    'AorDetail': {
        'max_contacts': 'MaxContacts',
        'contacts_registered': 'ContactsRegistered'
    },
    'ContactStatusDetail': {
        'uri': 'URI',
        'user_agent': 'UserAgent',
        'via_address': 'ViaAddress',
        'status': 'Status'
    }
}

# Events to skip in the response
SKIP_EVENTS = ['EndpointDetailComplete']

def filter_event(event: dict, event_type: str) -> dict:
    """
    Filter an event based on the configured parameters
    """
    if event_type not in EVENT_FILTERS:
        return {}
        
    filtered = {}
    for new_key, original_key in EVENT_FILTERS[event_type].items():
        value = event.get(original_key, '')
        if value:  # Only include non-empty values
            filtered[new_key] = value
            
    return filtered
