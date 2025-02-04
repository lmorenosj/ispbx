import asyncio
from ami_client import AmiClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ami_connection():
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
        
        # Get detailed information about endpoint 101
        logger.info("Getting detailed information for endpoint 101...")
        details = await ami.get_endpoint_details("101")
        logger.info(f"Endpoint exists in config: {details['exists_in_config']}")
        logger.info(f"Endpoint details: {details['response']}")
        
        # Get current state and registration
        logger.info("\nGetting current state and registration...")
        status = await ami.get_endpoint_state("101")
        reg_status = await ami.get_endpoint_registration("101")
        logger.info(f"Current state: {status}")
        logger.info(f"Registration status: {reg_status}")
        
    except Exception as e:
        logger.error(f"Error during AMI test: {e}")
    finally:
        # Clean up
        logger.info("Closing AMI connection...")
        await ami.close()
        logger.info("AMI connection closed.")

if __name__ == "__main__":
    asyncio.run(test_ami_connection())
