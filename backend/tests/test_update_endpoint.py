#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def update_endpoint():
    """Test updating an endpoint's caller 
    ID"""
    
    # API endpoint URL
    url = "http://localhost:8000/api/endpoints/100"
    
    # Data to update - changing the name to user100_updated
    update_data2 = {
        "name": "user100"
    }

    update_data = {
        "extension": "100",
        "name": "user100abc",
        "context": "Available",
        "allow": "ulaw,alaw",
        "disallow": "all"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Send PUT request to update the endpoint
            logger.info(f"Sending update request to {url} with data: {update_data}")
            async with session.put(url, json=update_data) as response:
                # Get response data
                status = response.status
                response_data = await response.json()
                
                # Log the response
                logger.info(f"Response status: {status}")
                logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
                
                # Check if update was successful
                if status == 200 and response_data.get("status") == "success":
                    logger.info("✅ Endpoint update successful!")
                else:
                    logger.error(f"❌ Endpoint update failed: {response_data.get('message', 'Unknown error')}")
                    
    except Exception as e:
        logger.error(f"Error during endpoint update test: {e}")

if __name__ == "__main__":
    # Run the async test function
    asyncio.run(update_endpoint())
