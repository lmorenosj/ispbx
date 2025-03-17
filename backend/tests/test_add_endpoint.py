#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def add_endpoint():
    """Test adding a new endpoint"""
    
    # API endpoint URL
    url = "http://localhost:8000/api/endpoints"
    
    # Data for the new endpoint
    endpoint_data = {
        'extension': '131',
        'name': 'user131',
        'context': 'from-internal',
        'password': '131pass'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Send POST request to create the endpoint
            logger.info(f"Sending create request to {url} with data: {endpoint_data}")
            async with session.post(url, json=endpoint_data) as response:
                # Get response data
                status = response.status
                response_data = await response.json()
                
                # Log the response
                logger.info(f"Response status: {status}")
                logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
                
                # Check if creation was successful
                if status == 201 and response_data.get("status") == "success":
                    logger.info("✅ Endpoint creation successful!")
                else:
                    logger.error(f"❌ Endpoint creation failed: {response_data.get('message', 'Unknown error')}")
                    
    except Exception as e:
        logger.error(f"Error during endpoint creation test: {e}")

if __name__ == "__main__":
    # Run the async test function
    asyncio.run(add_endpoint())
