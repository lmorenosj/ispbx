from typing import Dict, List, Optional
from panoramisk import Manager

from .logger import logger, ami_response_logger
from .formatter import format_ami_response
from .utils import extract_extension, parse_rtcp_stats
from .parser import parse_endpoint_list, parse_endpoint_detail, parse_registration_status, parse_active_calls

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
                logger.info("Connected to Asterisk AMI")
                
                # Register event handlers
                if self.event_callback:
                    # Register for each event type separately
                    for event in ['PeerStatus', 'DeviceStateChange', 'Newchannel', 'Hangup', 'Bridge', 'Dial']:
                        self.manager.register_event(event, self._handle_event)
                    logger.info("Registered AMI event handlers")
            except Exception as e:
                logger.error(f"Failed to connect to AMI: {e}")
                raise

    async def _handle_event(self, event):
        """Handle AMI events and forward them to the callback"""
        if self.event_callback:
            event_type = event.get('Event')
            event_data = dict(event)
            await self.event_callback(event_type, event_data)

    async def close(self):
        """Close AMI connection"""
        if self._connected and self.manager:
            try:
                if hasattr(self.manager, 'protocol') and self.manager.protocol:
                    self.manager.protocol.transport.close()
                self._connected = False
                logger.info("Disconnected from Asterisk AMI")
            except Exception as e:
                logger.error(f"Error closing AMI connection: {e}")
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
            logger.error(f"Error getting endpoint details: {e}")
            raise


    async def _process_all_endpoints(self) -> Dict:
        """Parse and format response for all endpoints"""
        action = {'Action': 'PJSIPShowEndpoints'}
        response = await self.manager.send_action(action)
        ami_response_logger.info(format_ami_response('PJSIPShowEndpoints', response))
        # Convert Message objects to dictionaries
        response_list = [dict(event) for event in response]
        return {'endpoints': response_list}


    async def _process_single_endpoint(self, extension: str) -> Dict:
        """Get and parse details for a single endpoint"""
        action = {'Action': 'PJSIPShowEndpoint', 'Endpoint': extension}
        response = await self.manager.send_action(action)
        ami_response_logger.info(format_ami_response('PJSIPShowEndpoint', response))
        return parse_endpoint_detail(extension, response)



    async def get_endpoint_state(self, extension: str) -> str:
        """Get current state of an endpoint (e.g., 'ONLINE', 'OFFLINE')"""
        if not self._connected:
            await self.connect()

        try:
            action = {'Action': 'ExtensionState', 'Exten': str(extension)}
            response = await self.manager.send_action(action)
            ami_response_logger.info(format_ami_response('ExtensionState', response))

            if response:
                try:
                    status = response[0].get('Status', -1)
                    if isinstance(status, str):
                        status = int(status)
                    return str(self._map_extension_state(status))
                except (ValueError, TypeError):
                    return 'UNKNOWN'
            return 'UNKNOWN'
        except Exception as e:
            logger.error(f"Error getting endpoint state: {e}")
            return 'UNKNOWN'

    def _map_extension_state(self, state: int) -> str:
        """Map numeric extension state to string representation
        
        Args:
            state: Numeric state value
            
        Returns:
            str: Human-readable state
        """
        states = {
            0: 'IDLE',
            1: 'IN_USE',
            2: 'BUSY',
            4: 'UNAVAILABLE',
            8: 'RINGING',
            16: 'ON_HOLD'
        }
        return states.get(state, 'UNKNOWN')

    async def get_endpoint_registration(self, extension: str) -> Dict:
        """Get registration status and details for an endpoint"""
        if not self._connected:
            await self.connect()

        try:
            action = {'Action': 'PJSIPShowRegistrationInboundContactStatuses'}
            response = await self.manager.send_action(action)
            ami_response_logger.info(format_ami_response('PJSIPShowRegistrationInboundContactStatuses', response))
            return parse_registration_status(response, extension)
        except Exception as e:
            logger.error(f"Error getting registration status: {e}")
            raise

    async def get_active_calls(self) -> List[Dict]:
        """Get information about all active calls in the system"""
        if not self._connected:
            await self.connect()

        try:
            channels_response = await self.manager.send_action({'Action': 'CoreShowChannels'})
            ami_response_logger.info(format_ami_response('CoreShowChannels', channels_response))

            bridges_response = await self.manager.send_action({'Action': 'BridgeList'})
            ami_response_logger.info(format_ami_response('BridgeList', bridges_response))

            return parse_active_calls(channels_response, bridges_response)
        except Exception as e:
            logger.error(f"Error getting active calls: {e}")
            raise
