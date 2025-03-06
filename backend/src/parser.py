"""Parser module for AMI responses.

This module contains functions for parsing different types of AMI responses into structured data.
Each parser is specialized for a specific type of AMI response (endpoints, contacts, etc.).
"""

from typing import Dict, List, Optional
import re


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
                        'extension': parse_extension(channel)
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

def parse_extension(channel: str) -> str:
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


    return detailed_endpoints

def parse_endpoint_callerid(callerid: str) -> Dict:
    """Parse Callerid into name and extension
    
    Args:
        callerid: Callerid string in format "{Name}" <{extension}>
        
    Returns:
        Dict containing name and extension
    """
    name = ''
    extension = ''
    
    # Try to extract name from format "{Name}" <{extension}>
    import re
    match = re.match(r'^"([^"]*)"', callerid)
    if match:
        name = match.group(1)
    
    # Extract extension from format <{extension}>
    match = re.match(r'<(\d+)>', callerid)
    if match:
        extension = match.group(1)
    
    return {'name': name, 'extension': extension}

def parse_rtcp_stats(stats_str: str) -> dict:
    """Parse RTCP statistics string into a structured format
    
    Args:
        stats_str: Raw RTCP statistics string
        
    Returns:
        dict: Parsed RTCP statistics
    """
    stats = {}
    if not stats_str:
        return stats

    # Split stats into lines and parse each line
    lines = stats_str.split(';')
    for line in lines:
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Convert numeric values
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass
                
            stats[key] = value
            
    return stats

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


