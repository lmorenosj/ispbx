#!/usr/bin/env python3
# /home/ubuntu/Documents/ispbx/backend/tests/queue_api_test.py

import asyncio
import aiohttp
import logging
import json
import sys
import urllib.parse
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Base URL
API_BASE_URL = "http://localhost:8000/api"

async def test_queue_api():
    """Test the Queue API endpoints"""
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: List all queues
            logger.info("\n=== Testing List Queues API ===")
            queues = await list_queues(session)
            
            # Test 2: Create a test queue
            logger.info("\n=== Testing Create Queue API ===")
            test_queue_name = "test_queue"
            await create_queue(session, test_queue_name)
            
            # Test 3: Get queue details
            logger.info(f"\n=== Testing Get Queue Details API for {test_queue_name} ===")
            queue_details = await get_queue_details(session, test_queue_name)
            
            # Test 4: Update queue
            logger.info(f"\n=== Testing Update Queue API for {test_queue_name} ===")
            await update_queue(session, test_queue_name)
            
            # Test 5: Add member to queue
            logger.info(f"\n=== Testing Add Member to Queue API for {test_queue_name} ===")
            await add_queue_member(session, test_queue_name, "PJSIP/1001")
            
            # Test 6: List queue members
            logger.info(f"\n=== Testing List Queue Members API for {test_queue_name} ===")
            members = await list_queue_members(session, test_queue_name)
            
            # Test 7: Remove member from queue
            if members and len(members) > 0:
                member_interface = members[0].get('interface')
                if member_interface:
                    logger.info(f"\n=== Testing Remove Member from Queue API for {test_queue_name} ===")
                    await remove_queue_member(session, test_queue_name, member_interface)
            
            # Test 8: Delete queue
            logger.info(f"\n=== Testing Delete Queue API for {test_queue_name} ===")
            await delete_queue(session, test_queue_name)
            
        except Exception as e:
            logger.error(f"Error during queue API test: {e}")

async def list_queues(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """List all queues"""
    url = f"{API_BASE_URL}/queues"
    async with session.get(url) as response:
        data = await response.json()
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response data: {json.dumps(data, indent=2)}")
        
        if response.status == 200 and data.get("status") == "success":
            return data.get("queues", [])
        return []

async def create_queue(session: aiohttp.ClientSession, queue_name: str) -> bool:
    """Create a new queue"""
    url = f"{API_BASE_URL}/queues"
    payload = {
        "queue_name": queue_name,
        "strategy": "ringall",
        "timeout": 15,
        "musiconhold": "default",
        "announce": "",
        "context": "from-queue",
        "maxlen": 0,
        "servicelevel": 60,
        "wrapuptime": 0
    }
    
    async with session.post(url, json=payload) as response:
        data = await response.json()
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response data: {json.dumps(data, indent=2)}")
        
        return response.status == 201 and data.get("status") == "success"

async def get_queue_details(session: aiohttp.ClientSession, queue_name: str) -> Dict[str, Any]:
    """Get queue details"""
    url = f"{API_BASE_URL}/queues/{queue_name}"
    async with session.get(url) as response:
        data = await response.json()
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response data: {json.dumps(data, indent=2)}")
        
        if response.status == 200 and data.get("status") == "success":
            return data.get("queue", {})
        return {}

async def update_queue(session: aiohttp.ClientSession, queue_name: str) -> bool:
    """Update a queue"""
    url = f"{API_BASE_URL}/queues/{queue_name}"
    payload = {
        "strategy": "leastrecent",
        "timeout": 20,
        "musiconhold": "default",
        "announce": "queue-thankyou",
        "context": "from-queue",
        "maxlen": 10,
        "servicelevel": 30,
        "wrapuptime": 5
    }
    
    async with session.put(url, json=payload) as response:
        data = await response.json()
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response data: {json.dumps(data, indent=2)}")
        
        return response.status == 200 and data.get("status") == "success"

async def add_queue_member(session: aiohttp.ClientSession, queue_name: str, interface: str) -> bool:
    """Add a member to a queue"""
    url = f"{API_BASE_URL}/queues/{queue_name}/members"
    payload = {
        "interface": interface,
        "membername": "Test Member",
        "penalty": 0,
        "paused": 0,
        "wrapuptime": 0
    }
    
    async with session.post(url, json=payload) as response:
        data = await response.json()
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response data: {json.dumps(data, indent=2)}")
        
        return response.status == 201 and data.get("status") == "success"

async def list_queue_members(session: aiohttp.ClientSession, queue_name: str) -> List[Dict[str, Any]]:
    """List members of a queue"""
    url = f"{API_BASE_URL}/queues/{queue_name}/members"
    async with session.get(url) as response:
        data = await response.json()
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response data: {json.dumps(data, indent=2)}")
        
        if response.status == 200 and data.get("status") == "success":
            return data.get("members", [])
        return []

async def remove_queue_member(session: aiohttp.ClientSession, queue_name: str, interface: str) -> bool:
    """Remove a member from a queue"""
    # Use URL encoding for the interface parameter
    encoded_interface = urllib.parse.quote(interface)
    url = f"{API_BASE_URL}/queues/{queue_name}/members/{encoded_interface}"
    
    # Log the URL we're attempting to use
    logger.info(f"Attempting to remove member with URL: {url}")
    
    # Send the DELETE request
    async with session.delete(url) as response:
        data = await response.json()
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response data: {json.dumps(data, indent=2)}")
        
        return response.status == 200 and data.get("status") == "success"

async def delete_queue(session: aiohttp.ClientSession, queue_name: str) -> bool:
    """Delete a queue"""
    url = f"{API_BASE_URL}/queues/{queue_name}"
    async with session.delete(url) as response:
        data = await response.json()
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response data: {json.dumps(data, indent=2)}")
        
        return response.status == 200 and data.get("status") == "success"

def print_usage():
    print(f"Usage: python {sys.argv[0]}")
    print("Tests the queue API endpoints")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print_usage()
    else:
        asyncio.run(test_queue_api())
