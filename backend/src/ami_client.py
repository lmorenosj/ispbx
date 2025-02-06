import logging
from typing import Dict
from panoramisk import Manager

logger = logging.getLogger(__name__)

class AmiClient:
    def __init__(self, host: str = '127.0.0.1', port: int = 5038, username: str = 'admin', password: str = 'admin'):
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
            except Exception as e:
                logger.error(f"Failed to connect to AMI: {e}")
                raise

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
        """
        Get detailed information about a PJSIP endpoint or all endpoints if no extension is provided
        """
        try:
            if not self._connected:
                await self.connect()

            # Get list of all endpoints first
            endpoints = await self.manager.send_action({
                'Action': 'PJSIPShowEndpoints'
            })

            if extension is None:
                # Return all endpoints using only PJSIPShowEndpoints information
                all_endpoints = []
                if endpoints:
                    for event in endpoints:
                        if event.get('Event') == 'EndpointList':
                            ext = event.get('ObjectName')
                            if ext:
                                all_endpoints.append({
                                    'extension': ext,
                                    'exists_in_config': True,
                                    'response': event
                                })
                return {'endpoints': all_endpoints}
            else:
                # Get details for specific endpoint
                response = await self.manager.send_action({
                    'Action': 'PJSIPShowEndpoint',
                    'Endpoint': extension
                })

                # Check if endpoint exists in configuration
                exists = False
                if endpoints and 'EndpointList' in endpoints:
                    for endpoint in endpoints['EndpointList']:
                        if endpoint.get('ObjectName') == extension:
                            exists = True
                            break

                return {
                    'exists_in_config': exists,
                    'response': response
                }
        except Exception as e:
            logger.error(f"Error getting endpoint details: {e}")
            raise
