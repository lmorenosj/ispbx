import asyncio
from ami.client import AmiClient
import logging
import json
import sys
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_ami_connection():
    """Test AMI connection and get all endpoint details"""
    # Initialize AMI client with the same credentials as main.py
    ami = AmiClient(
        host='127.0.0.1',
        port=5038,
        username='admin',
        password='admin'
    )
    
    try:
        # Test connection
        logger.info("Attempting to connect to AMI...")
        await ami.connect()
        logger.info("Successfully connected to AMI!")
        
        # Get information about all endpoints or a specific endpoint
        extension = sys.argv[1] if len(sys.argv) > 1 else None
        
        if extension:
            logger.info(f"\nGetting information for extension {extension}...")
            details = await ami.get_endpoint_registration(extension)
        else:
            logger.info("\nGetting information for all endpoints...")
            details = await ami.get_endpoint_details()
        
        logger.info("\nRaw AMI Response:")
        logger.info(json.dumps(details, indent=2))
 
    except Exception as e:
        logger.error(f"Error during AMI test: {e}")
    finally:
        # Clean up
        logger.info("\nClosing AMI connection...")
        await ami.close()
        logger.info("AMI connection closed.")

def print_usage():
    print(f"Usage: python {sys.argv[0]} [extension]")
    print("Without an extension, shows all configured extensions")
    print("With an extension, shows details for that specific extension")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print_usage()
    asyncio.run(test_ami_connection())
