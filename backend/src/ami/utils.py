def extract_extension(channel: str) -> str:
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
