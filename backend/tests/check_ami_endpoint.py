#!/usr/bin/env python3
import asyncio
import logging
import json
from panoramisk import Manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_endpoint_creation():
    """Test creating a new endpoint via AMI and check if it's configured in Asterisk"""
    
    # Create AMI manager
    manager = Manager(
        host='127.0.0.1',
        port=5038,
        username='admin',
        secret='admin'
    )
    
    # Test endpoint details
    extension = '129'
    name = 'user129'
    password = '129pass'
    context = 'from-internal'
    
    # Section IDs
    section_id = extension
    auth_id = f"{section_id}-auth"
    aor_id = f"{section_id}-aor"
    
    try:
        # Connect to AMI
        await manager.connect()
        logger.info("Connected to AMI")
        
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
            delete_response = await manager.send_action(delete_action)
            logger.info(f"Delete section {section} response: {delete_response}")
            await asyncio.sleep(0.5)  # Increase delay to ensure operation completes
        
        # Create endpoint section
        logger.info(f"Creating endpoint section [{section_id}]...")
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
            'Value-000006': 'transport-udp',
            'Action-000007': 'Append',
            'Cat-000007': section_id,
            'Var-000007': 'disallow',
            'Value-000007': 'all',
            'Action-000008': 'Append',
            'Cat-000008': section_id,
            'Var-000008': 'allow',
            'Value-000008': 'ulaw,alaw',
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
        
        endpoint_response = await manager.send_action(endpoint_action)
        logger.info(f"Endpoint section creation response: {endpoint_response}")
        await asyncio.sleep(0.5)  # Wait for operation to complete
        
        # Create auth section
        logger.info(f"Creating auth section [{auth_id}]...")
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
        
        auth_response = await manager.send_action(auth_action)
        logger.info(f"Auth section creation response: {auth_response}")
        await asyncio.sleep(0.5)  # Wait for operation to complete
        
        # Create AOR section with template
        logger.info(f"Creating AOR section [{aor_id}]...")
        aor_action = {
            'Action': 'UpdateConfig',
            'SrcFilename': 'pjsip.conf',
            'DstFilename': 'pjsip.conf',
            'Reload': 'yes',  # Reload after all sections are created
            'Action-000000': 'NewCat',
            'Cat-000000': f"{aor_id}(assistance_aor)",  # Include template in section name
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
        
        aor_response = await manager.send_action(aor_action)
        logger.info(f"AOR section creation response: {aor_response}")
        
        # Reload PJSIP to apply changes
        reload_action = {'Action': 'PJSIPReload'}
        reload_response = await manager.send_action(reload_action)
        logger.info(f"PJSIP reload response: {reload_response}")
        
        # Wait for reload to complete
        await asyncio.sleep(1)
        
        # Verify endpoint creation
        logger.info("Checking PJSIP endpoints...")
        endpoints_response = await manager.send_action({'Action': 'PJSIPShowEndpoints'})
        
        # Log all endpoints for debugging
        logger.info("All endpoints from PJSIPShowEndpoints:")
        for event in endpoints_response:
            if 'ObjectName' in event:
                logger.info(f"Endpoint: {event['ObjectName']}")
        
        # Check if our new endpoint is in the list
        found = False
        for event in endpoints_response:
            if 'ObjectName' in event and event['ObjectName'] == extension:
                found = True
                logger.info(f"✅ Found endpoint {extension} in PJSIPShowEndpoints")
                logger.info(f"Details: {event}")
                break
                
        if not found:
            logger.warning(f"❌ Endpoint {extension} not found in PJSIPShowEndpoints")
            
            # Check pjsip.conf directly
            logger.info("Checking pjsip.conf configuration...")
            config_action = {
                'Action': 'GetConfig',
                'Filename': 'pjsip.conf'
            }
            logger.info(f"Sending GetConfig action: {config_action}")
            config_response = await manager.send_action(config_action)
            
            # Debug the config response
            logger.info(f"GetConfig response type: {type(config_response)}")
            logger.info(f"GetConfig response length: {len(config_response) if hasattr(config_response, '__len__') else 'N/A'}")
            
            # Log the first few events for debugging
            for i, event in enumerate(config_response):
                if i < 10:  # Only log the first 10 events to avoid flooding
                    logger.info(f"Config event {i}: {event}")
                else:
                    break
            
            # Look for endpoint 106 in the configuration
            found_in_config = False
            for event in config_response:
                if isinstance(event, dict) and 'Category' in event and event['Category'] == '106':
                    found_in_config = True
                    logger.info(f"✅ Found endpoint 106 in pjsip.conf")
                    logger.info(f"Config section: {event}")
                    break
                    
            if not found_in_config:
                logger.warning("❌ Endpoint 106 not found in pjsip.conf")
                
            # Try a direct query for the specific endpoint
            logger.info("Trying direct query for endpoint 106...")
            endpoint_action = {
                'Action': 'PJSIPShowEndpoint',
                'Endpoint': '106'
            }
            endpoint_response = await manager.send_action(endpoint_action)
            
            # Log the response
            logger.info(f"PJSIPShowEndpoint response type: {type(endpoint_response)}")
            logger.info(f"PJSIPShowEndpoint response length: {len(endpoint_response) if hasattr(endpoint_response, '__len__') else 'N/A'}")
            
            # Check if we got a valid response
            if endpoint_response:
                for event in endpoint_response:
                    logger.info(f"Endpoint 106 detail: {event}")
                    
                # Check if this was a successful response
                if any('Response' in event and event.get('Response') == 'Success' for event in endpoint_response):
                    logger.info("✅ Endpoint 106 exists according to PJSIPShowEndpoint")
                else:
                    logger.warning("❌ Endpoint 106 not found by PJSIPShowEndpoint")
        
    except Exception as e:
        logger.error(f"Error checking endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Disconnect from AMI
        manager.close()
        logger.info("Disconnected from AMI")

if __name__ == "__main__":
    # Run the async function
    asyncio.run(test_endpoint_creation())
