"""Parser module for AMI responses.

This module contains functions for parsing different types of AMI responses into structured data.
Each parser is specialized for a specific type of AMI response (endpoints, contacts, etc.).
"""

from typing import Dict, List, Optional

def parse_endpoint_list(response: List[Dict]) -> List[Dict]:
    """Parse endpoint list response into structured format
    
    Args:
        response: Raw response from PJSIPShowEndpoints action
        
    Returns:
        List of endpoint information dictionaries
    """
    endpoints = []
    if response:
        for event in response:
            if event.get('Event') == 'EndpointList':
                ext = event.get('ObjectName')
                if ext:
                    endpoint_info = {
                        'extension': ext,
                        'details': {
                            'endpoint': {
                                'DeviceState': event.get('DeviceState', 'Unknown'),
                            },
                            'aor': {
                                'Contacts': event.get('Contacts', '0'),
                            }
                        }
                    }
                    endpoints.append(endpoint_info)
    return endpoints

def parse_endpoint_detail(extension: str, response: List[Dict]) -> Dict:
    """Parse detailed endpoint response into structured format
    
    Args:
        extension: Extension number
        response: Combined response from multiple AMI actions
        
    Returns:
        Dict containing parsed endpoint information
    """
    endpoint_info = {
        'extension': str(extension),
        'exists_in_config': False,
        'details': {
            'endpoint': {},
            'auth': {},
            'aor': {},
            'contacts': []
        }
    }

    for event in response:
        event_type = str(event.get('Event', ''))
        
        if event_type == 'EndpointDetail':
            endpoint_info['exists_in_config'] = True
            endpoint_info['details']['endpoint'] = {
                'Context': str(event.get('Context', '')),
                'Codecs': str(event.get('Allow', '')),
                'DeviceState': str(event.get('DeviceState', 'Unknown')),
                'DirectMedia': str(event.get('DirectMedia', 'no')),
                'Transport': str(event.get('Transport', '')),
                'Aors': str(event.get('Aors', '')),
                'Auth': str(event.get('Auth', '')),
                'OutboundAuth': str(event.get('OutboundAuth', '')),
                'CallerID': str(event.get('Callerid', '')),
                'MailBoxes': str(event.get('Mailboxes', ''))
            }
        
        elif event_type == 'AuthDetail':
            endpoint_info['details']['auth'] = {
                'Username': str(event.get('Username', '')),
                'AuthType': str(event.get('AuthType', '')),
                'Password': str(event.get('Password', '')),
                'Realm': str(event.get('Realm', ''))
            }
        
        elif event_type == 'AorDetail':
            endpoint_info['details']['aor'] = {
                'Contacts': str(event.get('Contacts', '')),
                'MaxContacts': str(event.get('MaxContacts', '')),
                'ContactsRegistered': str(event.get('ContactsRegistered', '')),
                'DefaultExpiration': str(event.get('DefaultExpiration', '')),
                'MinimumExpiration': str(event.get('MinimumExpiration', '')),
                'MaximumExpiration': str(event.get('MaximumExpiration', '')),
                'QualifyFrequency': str(event.get('QualifyFrequency', '')),
                'QualifyTimeout': str(event.get('QualifyTimeout', ''))
            }
        
        elif event_type == 'ContactStatusDetail':
            contact = {
                'URI': str(event.get('URI', '')),
                'Status': str(event.get('Status', '')),
                'RoundtripUsec': str(event.get('RoundtripUsec', '')),
                'EndpointName': str(event.get('EndpointName', '')),
                'ViaAddress': str(event.get('ViaAddress', '')),
                'UserAgent': str(event.get('UserAgent', '')),
                'RegExpire': str(event.get('RegExpire', '')),
                'ID': str(event.get('ID', ''))
            }
            endpoint_info['details']['contacts'].append(contact)

    return endpoint_info

def parse_registration_status(response: List[Dict], extension: str) -> Dict:
    """Parse registration status response into structured format
    
    Args:
        response: Response from PJSIPShowRegistrationInboundContactStatuses action
        extension: Extension number to filter for
        
    Returns:
        Dict containing registration details
    """
    registration_info = {
        'registered': False,
        'address': '',
        'port': '',
        'user_agent': '',
        'expires': ''
    }

    if response:
        for event in response:
            event_type = str(event.get('Event', ''))
            aor = str(event.get('AOR', ''))
            if (event_type == 'ContactStatusDetail' and
                aor.startswith(str(extension))):
                registration_info.update({
                    'registered': str(event.get('Status', '')).lower() == 'reachable',
                    'address': str(event.get('ViaAddress', '')),
                    'port': str(event.get('ViaPort', '')),
                    'user_agent': str(event.get('UserAgent', '')),
                    'expires': str(event.get('RegExpire', ''))
                })
                break

    return registration_info

def parse_active_calls(channels_response: List[Dict], bridges_response: List[Dict]) -> List[Dict]:
    """Parse active calls response into structured format
    
    Args:
        channels_response: Response from CoreShowChannels action
        bridges_response: Response from BridgeList action
        
    Returns:
        List of active call information dictionaries
    """
    active_calls = []
    channels = {}
    bridges = {}

    # Process channels
    if channels_response:
        for event in channels_response:
            if event.get('Event') == 'CoreShowChannel':
                channel = event.get('Channel')
                if channel:
                    channels[channel] = {
                        'channel': channel,
                        'state': event.get('ChannelState'),
                        'caller_id': event.get('CallerIDNum'),
                        'connected_line': event.get('ConnectedLineNum'),
                        'duration': event.get('Duration'),
                        'extension': _extract_extension(channel)
                    }

    # Process bridges
    if bridges_response:
        for event in bridges_response:
            if event.get('Event') == 'BridgeList':
                bridge_id = event.get('BridgeUniqueid')
                if bridge_id:
                    bridges[bridge_id] = {
                        'id': bridge_id,
                        'technology': event.get('BridgeTechnology'),
                        'channels': []
                    }

    # Match channels to bridges and create call records
    for channel_data in channels.values():
        # Check if channel is in a bridge
        in_bridge = False
        for bridge in bridges.values():
            if channel_data['channel'] in bridge['channels']:
                in_bridge = True
                break

        if in_bridge:
            continue

        call_info = {
            'id': channel_data['channel'],
            'extension': channel_data['extension'],
            'state': channel_data['state'],
            'duration': channel_data['duration'],
            'caller_id': channel_data['caller_id'],
            'connected_line': channel_data['connected_line']
        }

        active_calls.append(call_info)

    return active_calls

def _extract_extension(channel: str) -> str:
    """Extract extension number from channel name
    
    Args:
        channel: Channel name (e.g., 'PJSIP/1001-00000001')
        
    Returns:
        str: Extracted extension number or empty string if not found
    """
    if not channel:
        return ''
    
    # Handle different channel name formats
    parts = channel.split('/')
    if len(parts) >= 2:
        extension = parts[1].split('-')[0]
        return extension
    return ''
