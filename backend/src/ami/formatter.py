from datetime import datetime
import json

def format_ami_response(action: str, response: any) -> str:
    """Format AMI response in a readable way
    
    Args:
        action: The AMI action that was performed
        response: The response data from AMI
        
    Returns:
        str: Formatted string representation of the AMI response
    """
    formatted = []
    formatted.append(f"[{datetime.now().strftime('%H:%M:%S')}] {action}")
    
    if isinstance(response, (list, tuple)):
        for item in response:
            if isinstance(item, dict):
                event = item.get('Event', '')
                if event:
                    # Only show the most relevant fields for each event type
                    if event == 'EndpointList':
                        formatted.append(f"  {event}: {item.get('ObjectName')} [{item.get('DeviceState')}]")
                    elif event == 'EndpointDetail':
                        formatted.append(f"  {event}: {item.get('ObjectName')} [Context: {item.get('Context')}, Codecs: {item.get('Allow')}]")
                    elif event == 'AuthDetail':
                        formatted.append(f"  {event}: {item.get('Username')} [{item.get('AuthType')}]")
                    elif event == 'AorDetail':
                        formatted.append(f"  {event}: Contacts={item.get('ContactsRegistered')}/{item.get('MaxContacts')}")
                    elif event in ['EndpointDetailComplete', 'EndpointListComplete', 'BridgeListComplete', 'CoreShowChannelsComplete']:
                        formatted.append(f"  {event}: {item.get('ListItems')} items")
                    else:
                        formatted.append(f"  {event}: {','.join([f'{k}={v}' for k,v in item.items() if k not in ['Event', 'ActionID', 'content'] and v])}")
                else:
                    # For non-event responses, only show if it's an error or has a message
                    resp = item.get('Response', '')
                    msg = item.get('Message', '')
                    if resp == 'Error' or msg:
                        formatted.append(f"  {resp}: {msg}")
            else:
                # For non-dict items, only show if they have content
                if hasattr(item, 'content') and item.content:
                    formatted.append(f"  Content: {item.content}")
                else:
                    formatted.append(f"  {str(item)}")
    elif isinstance(response, dict):
        # For single dictionary, only show relevant fields
        relevant = {k: v for k, v in response.items() if k not in ['ActionID', 'content'] and v}
        formatted.append(json.dumps(relevant, indent=2))
    else:
        # For single non-dict response, show content if available
        if hasattr(response, 'content') and response.content:
            formatted.append(f"Content: {response.content}")
        else:
            formatted.append(str(response))
    
    formatted.append("-" * 40)
    return "\n".join(formatted)
