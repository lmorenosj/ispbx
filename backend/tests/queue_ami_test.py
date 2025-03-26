#!/usr/bin/env python3
# /home/ubuntu/Documents/ispbx/backend/tests/queue_ami_test.py

import asyncio
import logging
import json
import sys
from typing import Dict, List, Any, Optional

# Add the parent directory to the path to find the ami module
import os
import sys

# Get the absolute path of the backend directory
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Add it to the Python path
sys.path.insert(0, backend_dir)

# Now import the AMI client
from src.ami.client import AmiClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QueueAmiTester:
    """Test Asterisk Queue functionality through AMI"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 5038,
                 username: str = 'admin', password: str = 'admin'):
        """Initialize the AMI client for queue testing"""
        self.ami = AmiClient(
            host=host,
            port=port,
            username=username,
            password=password
        )
        
    async def connect(self):
        """Connect to the AMI"""
        await self.ami.connect()
        logger.info("Successfully connected to AMI")
        
    async def close(self):
        """Close the AMI connection"""
        await self.ami.close()
        logger.info("AMI connection closed")
        
    async def get_queues(self) -> List[Dict[str, Any]]:
        """Get all queues through AMI"""
        logger.info("Getting all queues...")
        
        # Send QueueStatus command
        response = await self.ami.send_action({
            'Action': 'QueueStatus'
        })
        
        # Process the response to extract queue information
        queues = []
        current_queue = None
        
        for event in response:
            if event.get('Event') == 'QueueParams':
                queue_name = event.get('Queue')
                if queue_name:
                    current_queue = {
                        'name': queue_name,
                        'strategy': event.get('Strategy', ''),
                        'calls': event.get('Calls', '0'),
                        'max_wait': event.get('Holdtime', '0'),
                        'completed': event.get('Completed', '0'),
                        'abandoned': event.get('Abandoned', '0'),
                        'service_level': event.get('ServiceLevel', '0'),
                        'service_level_perf': event.get('ServiceLevelPerf', '0'),
                        'weight': event.get('Weight', '0'),
                        'members': []
                    }
                    queues.append(current_queue)
            
            elif event.get('Event') == 'QueueMember' and current_queue:
                if event.get('Queue') == current_queue['name']:
                    member = {
                        'interface': event.get('Interface', ''),
                        'name': event.get('Name', ''),
                        'state_interface': event.get('StateInterface', ''),
                        'membership': event.get('Membership', ''),
                        'penalty': event.get('Penalty', '0'),
                        'calls_taken': event.get('CallsTaken', '0'),
                        'last_call': event.get('LastCall', '0'),
                        'status': event.get('Status', ''),
                        'paused': event.get('Paused', '0') == '1',
                        'paused_reason': event.get('PausedReason', '')
                    }
                    current_queue['members'].append(member)
        
        return queues
    
    async def get_queue_details(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific queue"""
        logger.info(f"Getting details for queue: {queue_name}")
        
        queues = await self.get_queues()
        for queue in queues:
            if queue['name'] == queue_name:
                return queue
        
        return None
    
    async def add_queue(self, queue_name: str, strategy: str = 'ringall') -> bool:
        """Add a new queue using AMI"""
        logger.info(f"Adding queue: {queue_name} with strategy: {strategy}")
        
        # Use QueueAdd command to add a new queue
        response = await self.ami.send_action({
            'Action': 'QueueAdd',
            'Queue': queue_name,
            'Strategy': strategy
        })
        
        success = False
        for event in response:
            if event.get('Response') == 'Success':
                success = True
                break
        
        return success
    
    async def remove_queue(self, queue_name: str) -> bool:
        """Remove a queue using AMI"""
        logger.info(f"Removing queue: {queue_name}")
        
        # Use QueueRemove command to remove a queue
        response = await self.ami.send_action({
            'Action': 'QueueRemove',
            'Queue': queue_name
        })
        
        success = False
        for event in response:
            if event.get('Response') == 'Success':
                success = True
                break
        
        return success
    
    async def add_queue_member(self, queue_name: str, interface: str, 
                              member_name: str = None, penalty: int = 0) -> bool:
        """Add a member to a queue"""
        logger.info(f"Adding member {interface} to queue: {queue_name}")
        
        action = {
            'Action': 'QueueAdd',
            'Queue': queue_name,
            'Interface': interface,
            'Penalty': str(penalty)
        }
        
        if member_name:
            action['MemberName'] = member_name
        
        # Use QueueAdd command to add a member
        response = await self.ami.send_action(action)
        
        success = False
        for event in response:
            if event.get('Response') == 'Success':
                success = True
                break
        
        return success
    
    async def remove_queue_member(self, queue_name: str, interface: str) -> bool:
        """Remove a member from a queue"""
        logger.info(f"Removing member {interface} from queue: {queue_name}")
        
        # Use QueueRemove command to remove a member
        response = await self.ami.send_action({
            'Action': 'QueueRemove',
            'Queue': queue_name,
            'Interface': interface
        })
        
        success = False
        for event in response:
            if event.get('Response') == 'Success':
                success = True
                break
        
        return success
    
    async def pause_queue_member(self, queue_name: str, interface: str, 
                                paused: bool = True, reason: str = None) -> bool:
        """Pause or unpause a queue member"""
        status = "pausing" if paused else "unpausing"
        logger.info(f"{status.capitalize()} member {interface} in queue: {queue_name}")
        
        action = {
            'Action': 'QueuePause',
            'Queue': queue_name,
            'Interface': interface,
            'Paused': 'true' if paused else 'false'
        }
        
        if reason and paused:
            action['Reason'] = reason
        
        # Use QueuePause command to pause/unpause a member
        response = await self.ami.send_action(action)
        
        success = False
        for event in response:
            if event.get('Response') == 'Success':
                success = True
                break
        
        return success

async def run_queue_ami_tests():
    """Run a series of tests for queue functionality through AMI"""
    tester = QueueAmiTester()
    
    try:
        # Connect to AMI
        await tester.connect()
        
        # Test 1: Get all queues
        logger.info("\n=== Test 1: Get All Queues ===")
        queues = await tester.get_queues()
        logger.info(f"Found {len(queues)} queues:")
        for queue in queues:
            logger.info(f"Queue: {queue['name']}, Strategy: {queue['strategy']}, Members: {len(queue['members'])}")
        
        # Test 2: Add a test queue
        test_queue_name = "test_ami_queue"
        logger.info(f"\n=== Test 2: Add Queue {test_queue_name} ===")
        add_result = await tester.add_queue(test_queue_name, "ringall")
        logger.info(f"Add queue result: {'Success' if add_result else 'Failed'}")
        
        # Test 3: Get queue details
        logger.info(f"\n=== Test 3: Get Queue Details for {test_queue_name} ===")
        queue_details = await tester.get_queue_details(test_queue_name)
        if queue_details:
            logger.info(f"Queue details: {json.dumps(queue_details, indent=2)}")
        else:
            logger.warning(f"Queue {test_queue_name} not found")
        
        # Test 4: Add a member to the queue
        test_interface = "PJSIP/1001"
        logger.info(f"\n=== Test 4: Add Member {test_interface} to Queue {test_queue_name} ===")
        add_member_result = await tester.add_queue_member(
            test_queue_name, 
            test_interface, 
            "Test Member", 
            0
        )
        logger.info(f"Add member result: {'Success' if add_member_result else 'Failed'}")
        
        # Test 5: Get updated queue details
        logger.info(f"\n=== Test 5: Get Updated Queue Details for {test_queue_name} ===")
        updated_queue = await tester.get_queue_details(test_queue_name)
        if updated_queue:
            logger.info(f"Updated queue details: {json.dumps(updated_queue, indent=2)}")
            
            # Test 6: Pause a queue member
            if updated_queue.get('members'):
                logger.info(f"\n=== Test 6: Pause Member {test_interface} ===")
                pause_result = await tester.pause_queue_member(
                    test_queue_name,
                    test_interface,
                    True,
                    "Testing pause functionality"
                )
                logger.info(f"Pause member result: {'Success' if pause_result else 'Failed'}")
                
                # Test 7: Unpause a queue member
                logger.info(f"\n=== Test 7: Unpause Member {test_interface} ===")
                unpause_result = await tester.pause_queue_member(
                    test_queue_name,
                    test_interface,
                    False
                )
                logger.info(f"Unpause member result: {'Success' if unpause_result else 'Failed'}")
                
                # Test 8: Remove a queue member
                logger.info(f"\n=== Test 8: Remove Member {test_interface} ===")
                remove_member_result = await tester.remove_queue_member(
                    test_queue_name,
                    test_interface
                )
                logger.info(f"Remove member result: {'Success' if remove_member_result else 'Failed'}")
        
        # Test 9: Remove the test queue
        logger.info(f"\n=== Test 9: Remove Queue {test_queue_name} ===")
        remove_result = await tester.remove_queue(test_queue_name)
        logger.info(f"Remove queue result: {'Success' if remove_result else 'Failed'}")
        
    except Exception as e:
        logger.error(f"Error during AMI queue tests: {e}")
    finally:
        # Clean up
        await tester.close()

def print_usage():
    print(f"Usage: python {sys.argv[0]}")
    print("Tests the queue functionality through AMI")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print_usage()
    else:
        asyncio.run(run_queue_ami_tests())
