# /home/ubuntu/Documents/ispbx/backend/src/client.py

from typing import Dict, List, Optional
from panoramisk import Manager
from parser import parse_endpoint_callerid, parse_active_calls
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmiClient:
    """Client for interacting with Asterisk Manager Interface (AMI)
    
    This class provides a high-level interface for connecting to and interacting with
    the Asterisk Manager Interface, handling events, and managing endpoint states.
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 5038,
                 username: str = 'admin', password: str = 'admin',
                 event_callback=None):
        """Initialize AMI client
        
        Args:
            host: AMI server hostname
            port: AMI server port
            username: AMI username
            password: AMI password
            event_callback: Optional callback for handling AMI events
        """
        self.event_callback = event_callback
        self.manager = Manager(
            host=host,
            port=port,
            username=username,
            secret=password,  # Panoramisk uses 'secret' instead of 'password'
            ping_delay=10  # Ping every 10 seconds to keep connection alive
        )
        self._connected = False

    async def connect(self):
        """Connect to Asterisk AMI"""
        if not self._connected:
            try:
                await self.manager.connect()
                self._connected = True
                logger.info("Connected to AMI")
                # Register event handlers
                if self.event_callback:
                    # Register for each event type separately
                    for event in ['PeerStatus', 'DeviceStateChange', 'Newchannel', 'Hangup', 'Bridge', 'Dial']:
                        self.manager.register_event(event, self._handle_event)
            except Exception as e:
                raise

    async def _handle_event(self, manager, event):
        """Handle AMI events and forward them to the callback"""
        if self.event_callback:
            event_type = event.get('Event')
            event_data = dict(event)
            await self.event_callback(event_type, event_data)
            # Broadcast the event to Socket.IO clients
            #logger.info(f"Broadcasting event: {event_type}")
            #await broadcast_event(event_type, event_data)

    async def close(self):
        """Close AMI connection"""
        if self._connected and self.manager:
            try:
                if hasattr(self.manager, 'protocol') and self.manager.protocol:
                    self.manager.protocol.transport.close()
                self._connected = False
                logger.info("Disconnected from AMI")
            except Exception as e:
                raise

    async def get_endpoint_details(self, extension: str = None) -> Dict:
        """Get endpoint details, either all endpoints or a specific one"""
        if not self._connected:
            await self.connect()

        try:
            if extension:
                return await self._process_single_endpoint(extension)
            else:
                return await self._process_all_endpoints()

        except Exception as e:
            raise

    async def _process_all_endpoints(self) -> Dict:
        """Parse and format response for all endpoints with detailed information"""
        # Get list of endpoints
        endpoints_action = {'Action': 'PJSIPShowEndpoints'}
        endpoints_response = await self.manager.send_action(endpoints_action)
        
        # Prepare detailed endpoints list
        detailed_endpoints = []
        
        # Iterate through endpoints and get detailed information
        for event in endpoints_response:
            endpoint_name = event.get('ObjectName', '')
            if not endpoint_name:
                continue
            
            # Get detailed endpoint information
            endpoint_detail_action = {
                'Action': 'PJSIPShowEndpoint',
                'Endpoint': endpoint_name
            }
            endpoint_detail_response = await self.manager.send_action(endpoint_detail_action)
            
            # Extract name from Callerid
            callerid = next((detail.get('Callerid', '') for detail in endpoint_detail_response if 'Callerid' in detail), '')           
            # Prepare endpoint details
            endpoint_info = {
                'Extension': endpoint_name,
                'Name': parse_endpoint_callerid(callerid)['name'],
                'State': event.get('DeviceState', 'Unknown')  # Use DeviceState directly from PJSIPShowEndpoints
            }   
            
            detailed_endpoints.append(endpoint_info)
        
        return {'endpoints': detailed_endpoints, 'details': None}

    async def _process_single_endpoint(self, extension: str) -> Dict:
        """Get and parse details for a single endpoint"""
        action = {'Action': 'PJSIPShowEndpoint', 'Endpoint': extension}
        response = await self.manager.send_action(action)
        
        # Extract specific details from the response
        agent = next((detail.get('UserAgent', '') for detail in response if 'UserAgent' in detail), '')
        expiration = next((detail.get('regExpire', '') for detail in response if 'regExpire' in detail), '')
        via_address = next((detail.get('ViaAddress', '') for detail in response if 'ViaAddress' in detail), '')
        callerid = next((detail.get('Callerid', '') for detail in response if 'Callerid' in detail), '')
        # Prepare endpoint info
        endpoints = {
            'Extension': extension,
            'Name': parse_endpoint_callerid(callerid)['name'],
            'State': next((detail.get('DeviceState', '') for detail in response if 'DeviceState' in detail), 'Unknown'),
        }
        
        # Prepare endpoint details
        endpoint_details = {
            'Extension': extension,
            'Agent': agent,
            'Expiration': expiration,
            'ViaAddress': via_address,
        }
        
        return {'endpoints': [endpoints], 'details': endpoint_details}

    async def get_endpoint_state(self, extension: str) -> Dict:
        """Get current state of an endpoint"""
        if not self._connected:
            await self.connect()

        try:
            action = {'Action': 'ExtensionState', 'Exten': str(extension)}
            response = await self.manager.send_action(action)

            # Use next() to extract the first response or return a default
            endpoint_status = next((
                {
                    'status': detail.get('Status', -1),
                    'statusText': detail.get('StatusText', 'Unknown')
                } 
                for detail in response if detail
            ), {
                'status': -1, 
                'statusText': 'Error at getting endpoint state'
            })

            return endpoint_status

        except Exception as e:
            return {
                'status': -1,
                'statusText': 'Error at getting endpoint state'
            }

    async def get_active_calls(self) -> List[Dict]:
        """Get information about all active calls in the system"""
        if not self._connected:
            await self.connect()

        try:
            channels_response = await self.manager.send_action({'Action': 'CoreShowChannels'})

            bridges_response = await self.manager.send_action({'Action': 'BridgeList'})

            return parse_active_calls(channels_response, bridges_response)
        except Exception as e:
            raise

    async def _handle_extension_status(self, event: Dict):
        """Handle ExtensionStatus events and track extension state changes
        
        Args:
            event: Raw AMI event dictionary
        """
        try:
            extension = event.get('Exten', '')
            status = event.get('Status', -1)
            status_text = event.get('StatusText', 'Unknown')
            context = event.get('Context', '')
            
            # Prepare event data
            extension_status = {
                'extension': extension,
                'status': status,
                'statusText': status_text,
                'context': context
            }
            
            # Broadcast the event if a callback is set
            if self.event_callback:
                await self.event_callback('ExtensionStatus', extension_status)
        
        except Exception as e:
            pass

    def register_event_handlers(self):
        """Register event handlers for various AMI events"""
        # Register ExtensionStatus event handler
        self.manager.register_event('ExtensionStatus', self._handle_extension_status)