# /home/ubuntu/Documents/ispbx/backend/src/client.py

from typing import Dict, List, Optional
import configparser
import io
import asyncio
from panoramisk import Manager
from parser import parse_endpoint_callerid, parse_active_calls
import logging
import re
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
                    for event in [
                        'DeviceStateChange', 'Newchannel', 'DialState', 'Newstate', 'DialEnd', 'Hangup'
                    ]:
                        self.manager.register_event(event, self._handle_event)
                    # Log successful registration
                    logger.info("Successfully registered all AMI events")
            except Exception as e:
                raise

    async def _handle_event(self, manager, event):
        """Handle AMI events and forward them to the callback"""
        if self.event_callback:
            event_type = event.get('Event')
            event_data = dict(event)
            
            # Enhanced logging for all AMI events
            logger.info(f"Received AMI event: {event_type}")
            logger.debug(f"AMI event details: {event_data}")
            
            # Log detailed event information for important events
            if event_type in ['DeviceStateChange', 'Dial', 'Newstate', 'Newchannel', 'Hangup', 'DialState', 'DialEnd']:
                logger.info(f"Important AMI event: {event_type} - DATA: {event_data}")
                
            try:
                await self.event_callback(event_type, event_data)
                logger.debug(f"Successfully processed event {event_type}")
            except Exception as e:
                logger.error(f"Error in event callback for {event_type}: {str(e)}")
                
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
        
        # Check if endpoint exists
        endpoint_exists = False
        for event in response:
            if 'ObjectName' in event and event.get('ObjectName') == extension:
                endpoint_exists = True
                break
            if 'Response' in event and event.get('Response') == 'Error':
                # If there's an error response, the endpoint likely doesn't exist
                return {'endpoints': [], 'details': None}
        
        if not endpoint_exists:
            # Return empty result if endpoint doesn't exist
            return {'endpoints': [], 'details': None}
        
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

    async def add_endpoint(self, endpoint_data: Dict) -> Dict:
        """Add a new endpoint configuration to pjsip.conf
        
        Args:
            endpoint_data: Dictionary containing endpoint configuration parameters
                Required keys:
                - extension: The endpoint extension number
                - name: The caller ID name
                - password: Authentication password
                - context: Dialplan context for incoming calls
                Optional keys:
                - transport: SIP transport (default: 'transport-udp')
                - allow: Allowed codecs (default: 'ulaw,alaw')
                - disallow: Disallowed codecs (default: 'all')
        
        Returns:
            Dict: Result of the operation with status and message
        """
        if not self._connected:
            await self.connect()
            
        try:
            # Extract required parameters
            extension = endpoint_data.get('extension')
            name = endpoint_data.get('name')
            password = endpoint_data.get('password')
            context = endpoint_data.get('context', 'from-internal')
            
            # Validate required parameters
            if not all([extension, name, password]):
                return {
                    'status': 'error',
                    'message': 'Missing required parameters: extension, name, and password are required'
                }
                
            # Extract optional parameters with defaults
            transport = endpoint_data.get('transport', 'transport-udp')
            allow = endpoint_data.get('allow', 'ulaw,alaw')
            disallow = endpoint_data.get('disallow', 'all')
            
            # Use the same section name for all three types (endpoint, auth, and AOR)
            # This follows the pattern of endpoint 110 which is working correctly
            section_id = extension
            
            # The endpoint will reference the auth and AOR sections with specific names
            auth_id = f"{section_id}"
            aor_id = f"{section_id}"
            
            # Create endpoint section
            endpoint_section = f"[{section_id}]\n"
            endpoint_section += "type = endpoint\n"
            endpoint_section += f"callerid = {name}<{extension}>\n"
            endpoint_section += f"auth = {auth_id}\n"
            endpoint_section += f"aors = {aor_id}\n"
            endpoint_section += f"context = {context}\n"
            endpoint_section += f"transport = {transport}\n"
            endpoint_section += "disallow = all\n"
            endpoint_section += "allow = ulaw,alaw\n"
            endpoint_section += "rewrite_contact = yes\n"
            endpoint_section += "direct_media = no\n"
            endpoint_section += "rtp_symmetric = yes\n"
            endpoint_section += "force_rport = yes\n"
            endpoint_section += "identify_by = username\n"
            
            # Create auth section
            auth_section = f"[{auth_id}]\n"
            auth_section += "type = auth\n"
            auth_section += "auth_type = userpass\n"
            auth_section += f"password = {password}\n"
            auth_section += f"username = {extension}\n"
            
            # Create AOR section with template
            aor_section = f"[{aor_id}](assistance_aor)\n"
            # Note: The template will provide the base settings, but we still need to specify the type
            aor_section += "type = aor\n"
            aor_section += "max_contacts = 1\n"
            aor_section += "qualify_frequency = 60\n"
            aor_section += "remove_existing = true\n"
            
            # Combine all sections
            config_content = f"{endpoint_section}\n{auth_section}\n{aor_section}\n"
            
            # First delete existing sections if they exist
            sections_to_delete = [section_id, auth_id, aor_id]
            for section in sections_to_delete:
                delete_action = {
                    'Action': 'UpdateConfig',
                    'SrcFilename': 'pjsip.conf',
                    'DstFilename': 'pjsip.conf',
                    'Reload': 'no',
                    'Action-000000': 'DelCat',
                    'Cat-000000': section
                }
                delete_response = await self.manager.send_action(delete_action)
                logger.info(f"Delete section {section} response: {delete_response}")
                await asyncio.sleep(0.5)  # Increase delay to ensure operation completes
            
            # Create endpoint section
            endpoint_action = {
                'Action': 'UpdateConfig',
                'SrcFilename': 'pjsip.conf',
                'DstFilename': 'pjsip.conf',
                'Reload': 'no',  # Don't reload until all sections are created
                'Action-000000': 'NewCat',
                'Cat-000000': section_id,
                'Action-000001': 'Append',
                'Cat-000001': section_id,
                'Var-000001': 'type',
                'Value-000001': 'endpoint',
                'Action-000002': 'Append',
                'Cat-000002': section_id,
                'Var-000002': 'callerid',
                'Value-000002': f"{name}<{extension}>",
                'Action-000003': 'Append',
                'Cat-000003': section_id,
                'Var-000003': 'auth',
                'Value-000003': auth_id,
                'Action-000004': 'Append',
                'Cat-000004': section_id,
                'Var-000004': 'aors',
                'Value-000004': aor_id,
                'Action-000005': 'Append',
                'Cat-000005': section_id,
                'Var-000005': 'context',
                'Value-000005': context,
                'Action-000006': 'Append',
                'Cat-000006': section_id,
                'Var-000006': 'transport',
                'Value-000006': transport,
                'Action-000007': 'Append',
                'Cat-000007': section_id,
                'Var-000007': 'disallow',
                'Value-000007': disallow,
                'Action-000008': 'Append',
                'Cat-000008': section_id,
                'Var-000008': 'allow',
                'Value-000008': allow,
                'Action-000009': 'Append',
                'Cat-000009': section_id,
                'Var-000009': 'rewrite_contact',
                'Value-000009': 'yes',
                'Action-000010': 'Append',
                'Cat-000010': section_id,
                'Var-000010': 'direct_media',
                'Value-000010': 'no',
                'Action-000011': 'Append',
                'Cat-000011': section_id,
                'Var-000011': 'rtp_symmetric',
                'Value-000011': 'yes',
                'Action-000012': 'Append',
                'Cat-000012': section_id,
                'Var-000012': 'force_rport',
                'Value-000012': 'yes',
                'Action-000013': 'Append',
                'Cat-000013': section_id,
                'Var-000013': 'identify_by',
                'Value-000013': 'username'
            }
            
            endpoint_response = await self.manager.send_action(endpoint_action)
            logger.info(f"Endpoint section creation response: {endpoint_response}")
            await asyncio.sleep(0.5)  # Wait for operation to complete
            
            # Check if endpoint creation was successful
            response_match = re.search(r"Response='(.*?)'", str(endpoint_response))
            if response_match and response_match.group(1).lower() == "error":
                message_match = re.search(r"Message='(.*?)'", str(endpoint_response))
                message = message_match.group(1) if message_match else "Unknown error"
                return {
                    "status": "error",
                    "message": f"Failed to create endpoint section: {message}"
                }
            
            # Create auth section
            auth_action = {
                'Action': 'UpdateConfig',
                'SrcFilename': 'pjsip.conf',
                'DstFilename': 'pjsip.conf',
                'Reload': 'no',
                'Action-000000': 'NewCat',
                'Cat-000000': auth_id,
                'Action-000001': 'Append',
                'Cat-000001': auth_id,
                'Var-000001': 'type',
                'Value-000001': 'auth',
                'Action-000002': 'Append',
                'Cat-000002': auth_id,
                'Var-000002': 'auth_type',
                'Value-000002': 'userpass',
                'Action-000003': 'Append',
                'Cat-000003': auth_id,
                'Var-000003': 'password',
                'Value-000003': password,
                'Action-000004': 'Append',
                'Cat-000004': auth_id,
                'Var-000004': 'username',
                'Value-000004': extension
            }
            
            auth_response = await self.manager.send_action(auth_action)
            logger.info(f"Auth section creation response: {auth_response}")
            await asyncio.sleep(0.5)  # Wait for operation to complete
            
            # Check if auth creation was successful
            response_match = re.search(r"Response='(.*?)'", str(auth_response))
            if response_match and response_match.group(1).lower() == "error":
                message_match = re.search(r"Message='(.*?)'", str(auth_response))
                message = message_match.group(1) if message_match else "Unknown error"
                return {
                    "status": "error",
                    "message": f"Failed to create auth section: {message}"
                }
            
            # Create AOR section with template
            aor_action = {
                'Action': 'UpdateConfig',
                'SrcFilename': 'pjsip.conf',
                'DstFilename': 'pjsip.conf',
                'Reload': 'yes',  # Reload after all sections are created
                'Action-000000': 'NewCat',
                'Cat-000000': f"{aor_id}",  # Include template in section name
                'Action-000001': 'Append',
                'Cat-000001': aor_id,
                'Var-000001': 'type',
                'Value-000001': 'aor',
                'Action-000002': 'Append',
                'Cat-000002': aor_id,
                'Var-000002': 'max_contacts',
                'Value-000002': '1',
                'Action-000003': 'Append',
                'Cat-000003': aor_id,
                'Var-000003': 'qualify_frequency',
                'Value-000003': '60',
                'Action-000004': 'Append',
                'Cat-000004': aor_id,
                'Var-000004': 'remove_existing',
                'Value-000004': 'true'
            }
            
            aor_response = await self.manager.send_action(aor_action)
            logger.info(f"AOR section creation response: {aor_response}")
            
            # Check if AOR creation was successful
            response_match = re.search(r"Response='(.*?)'", str(aor_response))
            response = response_match.group(1) if response_match else ""
            message_match = re.search(r"Message='(.*?)'", str(aor_response))
            message = message_match.group(1) if message_match else "Unknown error"

            if response.lower() == "error":
                return {
                    "status": "error",
                    "message": f"Failed to create AOR section: {message}"
                }
            
            # Add extension to dialplan if needed
            await self._update_dialplan_for_endpoint(extension, context)
            
            # Reload PJSIP to apply changes
            reload_action = {'Action': 'PJSIPReload'}
            await self.manager.send_action(reload_action)
            
            return {
                'status': 'success',
                'message': f'Endpoint {extension} added successfully',
                'extension': extension
            }
            
        except Exception as e:
            logger.error(f"Error adding endpoint: {e}")
            return {
                'status': 'error',
                'message': f'Failed to add endpoint: {str(e)}'
            }

    async def update_endpoint(self, extension: str, endpoint_data: Dict) -> Dict:
        """Update an existing endpoint configuration in pjsip.conf
        
        Args:
            extension: The endpoint extension to update
            endpoint_data: Dictionary containing endpoint configuration parameters to update
                Possible keys:
                - name: The caller ID name
                - password: Authentication password
                - context: Dialplan context for incoming calls
                - transport: SIP transport
                - allow: Allowed codecs
                - disallow: Disallowed codecs
        
        Returns:
            Dict: Result of the operation with status and message
        """
        if not self._connected:
            await self.connect()
            
        try:
            # Check if endpoint exists
            endpoint_check = await self.get_endpoint_details(extension)
            if not endpoint_check.get('details'):
                return {
                    'status': 'error',
                    'message': f'Endpoint {extension} not found'
                }
                
            # Prepare update actions
            actions = {
                'Action': 'UpdateConfig',
                'SrcFilename': 'pjsip.conf',
                'DstFilename': 'pjsip.conf',
                'Reload': 'yes'
            }
            
            action_index = 0
            
            # Update caller ID if provided
            if 'name' in endpoint_data:
                name = endpoint_data['name']
                actions[f'Action-{action_index:06d}'] = 'Update'
                actions[f'Cat-{action_index:06d}'] = extension
                actions[f'Var-{action_index:06d}'] = 'callerid'
                actions[f'Value-{action_index:06d}'] = f"{name}<{extension}>"
                action_index += 1
            
            # Update context if provided
            if 'context' in endpoint_data:
                context = endpoint_data['context']
                actions[f'Action-{action_index:06d}'] = 'Update'
                actions[f'Cat-{action_index:06d}'] = extension
                actions[f'Var-{action_index:06d}'] = 'context'
                actions[f'Value-{action_index:06d}'] = context
                action_index += 1
                
                # Update dialplan if context changed
                await self._update_dialplan_for_endpoint(extension, context)
            
            # Update transport if provided
            if 'transport' in endpoint_data:
                transport = endpoint_data['transport']
                actions[f'Action-{action_index:06d}'] = 'Update'
                actions[f'Cat-{action_index:06d}'] = extension
                actions[f'Var-{action_index:06d}'] = 'transport'
                actions[f'Value-{action_index:06d}'] = transport
                action_index += 1
            
            # Update allow codecs if provided
            if 'allow' in endpoint_data:
                allow = endpoint_data['allow']
                actions[f'Action-{action_index:06d}'] = 'Update'
                actions[f'Cat-{action_index:06d}'] = extension
                actions[f'Var-{action_index:06d}'] = 'allow'
                actions[f'Value-{action_index:06d}'] = allow
                action_index += 1
            
            # Update disallow codecs if provided
            if 'disallow' in endpoint_data:
                disallow = endpoint_data['disallow']
                actions[f'Action-{action_index:06d}'] = 'Update'
                actions[f'Cat-{action_index:06d}'] = extension
                actions[f'Var-{action_index:06d}'] = 'disallow'
                actions[f'Value-{action_index:06d}'] = disallow
                action_index += 1
            
            # Update password if provided
            if 'password' in endpoint_data:
                password = endpoint_data['password']
                actions[f'Action-{action_index:06d}'] = 'Update'
                actions[f'Cat-{action_index:06d}'] = extension  # Use extension name for auth section
                actions[f'Var-{action_index:06d}'] = 'password'
                actions[f'Value-{action_index:06d}'] = password
                action_index += 1
            
            # If no updates were provided
            if action_index == 0:
                return {
                    'status': 'warning',
                    'message': 'No changes provided for update'
                }
            
            # Send update action
            response = await self.manager.send_action(actions)
            
            # Check response
            if any('Response: Error' in str(r) for r in response):
                error_msg = next((r.get('Message', 'Unknown error') for r in response if 'Response: Error' in str(r)), 'Unknown error')
                return {
                    'status': 'error',
                    'message': f'Failed to update endpoint: {error_msg}'
                }
            
            # Reload PJSIP to apply changes
            reload_action = {'Action': 'PJSIPReload'}
            await self.manager.send_action(reload_action)
            
            return {
                'status': 'success',
                'message': f'Endpoint {extension} updated successfully',
                'extension': extension
            }
            
        except Exception as e:
            logger.error(f"Error updating endpoint: {e}")
            return {
                'status': 'error',
                'message': f'Failed to update endpoint: {str(e)}'
            }

    async def delete_endpoint(self, extension: str) -> Dict:
        """Delete an endpoint configuration from pjsip.conf
        
        Args:
            extension: The endpoint extension to delete
        
        Returns:
            Dict: Result of the operation with status and message
        """
        if not self._connected:
            await self.connect()
            
        try:
            # Check if endpoint exists using get_endpoint_config
            logger.info(f"Checking if endpoint {extension} exists before deletion")
            endpoint_config = await self.get_endpoint_config(extension)
            logger.info(f"Endpoint config before deletion: {endpoint_config}")
            
            # The endpoint config is nested inside the 'config' key
            if not endpoint_config.get('config', {}).get('endpoint'):
                logger.warning(f"Endpoint {extension} not found in configuration")
                return {
                    'status': 'error',
                    'message': f'Endpoint {extension} not found'
                }
                
            # Get the current configuration to determine the exact category names
            config = await self.get_endpoint_config(extension)
            if not config.get('config'):
                logger.warning(f"Cannot retrieve configuration for endpoint {extension}")
                return {
                    'status': 'error',
                    'message': f'Failed to delete endpoint: Cannot retrieve configuration'
                }
                
            # Use the actual category names from the configuration
            endpoint_section = extension
            auth_section = extension  # Use same name for auth section
            aor_section = extension  # Use same name for AOR section
            
            # Delete endpoint section
            endpoint_action = {
                'Action': 'UpdateConfig',
                'SrcFilename': 'pjsip.conf',
                'DstFilename': 'pjsip.conf',
                'Reload': 'yes',
                'Action-000000': 'DelCat',
                'Cat-000000': endpoint_section
            }
            
            logger.info(f"Deleting endpoint section {endpoint_section}")
            endpoint_response = await self.manager.send_action(endpoint_action)
            logger.info(f"Endpoint delete response: {endpoint_response}")
            
            # Delete auth section
            auth_action = {
                'Action': 'UpdateConfig',
                'SrcFilename': 'pjsip.conf',
                'DstFilename': 'pjsip.conf',
                'Reload': 'yes',
                'Action-000000': 'DelCat',
                'Cat-000000': auth_section
            }
            
            logger.info(f"Deleting auth section {auth_section}")
            auth_response = await self.manager.send_action(auth_action)
            logger.info(f"Auth delete response: {auth_response}")
            
            # Delete aor section
            aor_action = {
                'Action': 'UpdateConfig',
                'SrcFilename': 'pjsip.conf',
                'DstFilename': 'pjsip.conf',
                'Reload': 'yes',
                'Action-000000': 'DelCat',
                'Cat-000000': aor_section
            }
            
            logger.info(f"Deleting aor section {aor_section}")
            aor_response = await self.manager.send_action(aor_action)
            logger.info(f"AOR delete response: {aor_response}")
            
            # Check for errors in any of the responses
            all_responses = [endpoint_response, auth_response, aor_response]
            errors = [r.get('Message', 'Unknown error') for r in all_responses if 'Response: Error' in str(r)]
            
            if errors:
                logger.error(f"Errors in delete responses: {errors}")
                # Continue anyway, as some sections might have been deleted successfully
            
            # Remove from dialplan if needed
            await self._remove_endpoint_from_dialplan(extension)
            
            # Reload PJSIP to apply changes
            reload_action = {'Action': 'PJSIPReload'}
            await self.manager.send_action(reload_action)
            
            # Verify deletion was successful
            logger.info(f"Verifying deletion of endpoint {extension}")
            verification = await self.get_endpoint_config(extension)
            logger.info(f"Verification result: {verification}")
            
            if verification.get('config', {}).get('endpoint'):
                logger.warning(f"Endpoint {extension} still exists after deletion attempt")
                return {
                    'status': 'error',
                    'message': f'Failed to delete endpoint: Configuration still exists after deletion'
                }
            
            return {
                'status': 'success',
                'message': f'Endpoint {extension} deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting endpoint: {e}")
            return {
                'status': 'error',
                'message': f'Failed to delete endpoint: {str(e)}'
            }

    async def _update_dialplan_for_endpoint(self, extension: str, context: str) -> None:
        """Update the dialplan in extensions.conf for the endpoint
        
        This adds or updates the extension in the dialplan context
        """
        try:
            # Basic dialplan entry for the extension
            actions = {
                'Action': 'UpdateConfig',
                'SrcFilename': 'extensions.conf',
                'DstFilename': 'extensions.conf',
                'Reload': 'yes',
                'Action-000000': 'Update',
                'Cat-000000': context,
                'Var-000000': f'exten',
                'Value-000000': f'{extension},1,Dial(PJSIP/{extension})',
                'Action-000001': 'Update',
                'Cat-000001': context,
                'Var-000001': f'exten',
                'Value-000001': f'{extension},n,Hangup()'
            }
            
            # Send update action
            await self.manager.send_action(actions)
            
            # Reload dialplan
            reload_action = {'Action': 'DialplanReload'}
            await self.manager.send_action(reload_action)
            
        except Exception as e:
            logger.error(f"Error updating dialplan for endpoint {extension}: {e}")
            raise

