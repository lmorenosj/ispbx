#!/usr/bin/env python3
"""
Test script for deleting endpoints via the AMI client.
This script tests the delete_endpoint functionality of the AmiClient class.
"""

import asyncio
import logging
import os
import sys
from typing import Dict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BACKEND_DIR, 'src'))

# Import the AmiClient class
from client import AmiClient

async def test_delete_endpoint():
    """Test deleting an endpoint via the AMI client"""
    # Create AMI client
    ami_client = AmiClient(
        host=os.getenv('ASTERISK_HOST', '127.0.0.1'),
        port=int(os.getenv('ASTERISK_AMI_PORT', '5038')),
        username=os.getenv('ASTERISK_AMI_USER', 'admin'),
        password=os.getenv('ASTERISK_AMI_PASSWORD', 'admin')
    )
    
    try:
        # Connect to AMI
        await ami_client.connect()
        logger.info("Connected to AMI")
        
        # Test extension to delete
        extension = "107"
        

        # Now delete the endpoint
        logger.info(f"Deleting endpoint {extension}...")
        result = await ami_client.delete_endpoint(extension)
        
        if result['status'] == 'success':
            logger.info(f"Successfully deleted endpoint {extension}: {result['message']}")
            
            # Verify the endpoint was deleted
            endpoint_config = await ami_client.get_endpoint_config(extension)
            if not endpoint_config.get('config', {}).get('endpoint'):
                logger.info(f"Verified endpoint {extension} was deleted")
            else:
                logger.error(f"Endpoint {extension} still exists after deletion")
        else:
            logger.error(f"Failed to delete endpoint {extension}: {result['message']}")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
    finally:
        # Close the AMI connection
        await ami_client.close()
        logger.info("Closed AMI connection")

if __name__ == "__main__":
    asyncio.run(test_delete_endpoint())
