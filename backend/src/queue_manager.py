#!/usr/bin/env python3
# /home/ubuntu/Documents/ispbx/backend/src/queue_manager.py

import logging
import aiomysql
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QueueManager:
    """
    Manager for Asterisk queue operations using MySQL database.
    
    This class provides methods for creating, reading, updating, and deleting
    queues in the Asterisk database using MySQL.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 3306,
                 user: str = 'asteriskuser', password: str = 'asteriskpassword',
                 db: str = 'asterisk'):
        """
        Initialize the queue manager with database connection parameters.
        
        Args:
            host: MySQL server hostname
            port: MySQL server port
            user: MySQL username
            password: MySQL password
            db: MySQL database name
        """
        self.db_config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'db': db,
            'autocommit': True
        }
        self.pool = None
        self.ami_client = None  # Will be set externally
    
    async def connect(self):
        """Establish connection pool to the MySQL database"""
        if not self.pool:
            try:
                self.pool = await aiomysql.create_pool(**self.db_config)
                logger.info("Connected to MySQL database for queue management")
            except Exception as e:
                logger.error(f"Failed to connect to MySQL for queue management: {e}")
                raise
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            logger.info("Disconnected from MySQL database for queue management")
    
    async def create_queue(self, queue_name: str, strategy: str = 'ringall', 
                          timeout: int = 15, musiconhold: str = 'default',
                          announce: str = None, context: str = 'from-queue',
                          maxlen: int = 0, servicelevel: int = 60,
                          wrapuptime: int = 0) -> bool:
        """
        Create a new queue in the database.
        
        Args:
            queue_name: The name of the queue
            strategy: Queue strategy (ringall, leastrecent, fewestcalls, random, etc.)
            timeout: Ring timeout in seconds
            musiconhold: Music on hold class
            announce: Announcement to play
            context: Dialplan context for the queue
            maxlen: Maximum number of callers allowed in the queue (0 for unlimited)
            servicelevel: Service level threshold in seconds
            wrapuptime: Time in seconds after a call before agent can receive another call
            
        Returns:
            bool: True if queue was created successfully, False otherwise
        """
        if not self.pool:
            await self.connect()
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Create queue
                    query = """
                    INSERT INTO queues (
                        name, strategy, timeout, musiconhold, 
                        announce, context, maxlen, servicelevel, wrapuptime
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    await cursor.execute(
                        query,
                        (queue_name, strategy, timeout, musiconhold, 
                         announce, context, maxlen, servicelevel, wrapuptime)
                    )
                    
                    logger.info(f"Created queue {queue_name} with strategy '{strategy}'")
                    
                    # Trigger Asterisk to reload configuration
                    if self.ami_client:
                        try:
                            # Reload queue configuration
                            logger.info(f"Reloading queue configuration after queue creation")
                            reload_result = await self.ami_client.manager.send_action({
                                'Action': 'QueueReload',
                                'Queue': queue_name
                            })
                            logger.info(f"Queue configuration reloaded: {reload_result}")
                        except Exception as e:
                            logger.error(f"Failed to reload queue configuration: {e}")
                    else:
                        logger.warning("AMI client not set, unable to reload configuration")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to create queue {queue_name}: {e}")
            return False
    
    async def get_queue(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific queue.
        
        Args:
            queue_name: The name of the queue
            
        Returns:
            Dict containing queue details or None if not found
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get queue details
                    await cursor.execute(
                        "SELECT * FROM queues WHERE name = %s",
                        (queue_name,)
                    )
                    queue = await cursor.fetchone()
                    
                    if not queue:
                        return None
                    
                    # Get queue members
                    await cursor.execute(
                        "SELECT * FROM queue_members WHERE queue_name = %s",
                        (queue_name,)
                    )
                    members = await cursor.fetchall()
                    
                    # Combine details
                    result = {
                        'queue': queue,
                        'members': members
                    }
                    
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to get queue {queue_name}: {e}")
            return None
    
    async def list_queues(self) -> List[Dict[str, Any]]:
        """
        List all queues in the database.
        
        Returns:
            List of dictionaries containing basic queue information
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get all queues
                    await cursor.execute("SELECT name, strategy, timeout, musiconhold, maxlen FROM queues")
                    queues = await cursor.fetchall()
                    
                    # Get member counts for each queue
                    result = []
                    for queue in queues:
                        await cursor.execute(
                            "SELECT COUNT(*) as member_count FROM queue_members WHERE queue_name = %s",
                            (queue['name'],)
                        )
                        count = await cursor.fetchone()
                        queue['member_count'] = count['member_count'] if count else 0
                        result.append(queue)
                    
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to list queues: {e}")
            return []
    
    async def update_queue(self, queue_name: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing queue in the database.
        
        Args:
            queue_name: The name of the queue to update
            updates: Dictionary containing fields to update
            
        Returns:
            bool: True if queue was updated successfully, False otherwise
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Build update query dynamically based on provided fields
                    fields = []
                    values = []
                    
                    for key, value in updates.items():
                        if value is not None:
                            fields.append(f"{key} = %s")
                            values.append(value)
                    
                    if not fields:
                        logger.warning(f"No fields to update for queue {queue_name}")
                        return True
                    
                    # Add queue name to values
                    values.append(queue_name)
                    
                    # Execute update
                    query = f"UPDATE queues SET {', '.join(fields)} WHERE name = %s"
                    await cursor.execute(query, values)
                    
                    if cursor.rowcount == 0:
                        logger.warning(f"Queue {queue_name} not found or no changes made")
                        return False
                    
                    logger.info(f"Updated queue {queue_name}")
                    
                    # Trigger Asterisk to reload configuration
                    if self.ami_client:
                        try:
                            # Reload queue configuration
                            logger.info(f"Reloading queue configuration after queue update")
                            reload_result = await self.ami_client.manager.send_action({
                                'Action': 'QueueReload',
                                'Queue': queue_name
                            })
                            logger.info(f"Queue configuration reloaded: {reload_result}")
                        except Exception as e:
                            logger.error(f"Failed to reload queue configuration: {e}")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to update queue {queue_name}: {e}")
            return False
    
    async def delete_queue(self, queue_name: str) -> bool:
        """
        Delete a queue from the database.
        
        Args:
            queue_name: The name of the queue to delete
            
        Returns:
            bool: True if queue was deleted successfully, False otherwise
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Delete queue members first
                    await cursor.execute(
                        "DELETE FROM queue_members WHERE queue_name = %s",
                        (queue_name,)
                    )
                    
                    # Delete queue
                    await cursor.execute(
                        "DELETE FROM queues WHERE name = %s",
                        (queue_name,)
                    )
                    
                    if cursor.rowcount == 0:
                        logger.warning(f"Queue {queue_name} not found")
                        return False
                    
                    logger.info(f"Deleted queue {queue_name}")
                    
                    # Trigger Asterisk to reload configuration
                    if self.ami_client:
                        try:
                            # Reload queue configuration
                            logger.info(f"Reloading queue configuration after queue deletion")
                            reload_result = await self.ami_client.manager.send_action({
                                'Action': 'QueueReload'
                            })
                            logger.info(f"Queue configuration reloaded: {reload_result}")
                        except Exception as e:
                            logger.error(f"Failed to reload queue configuration: {e}")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to delete queue {queue_name}: {e}")
            return False
    
    async def add_queue_member(self, queue_name: str, interface: str, 
                              membername: str = None, penalty: int = 0,
                              paused: int = 0, wrapuptime: int = None) -> bool:
        """
        Add a member to a queue.
        
        Args:
            queue_name: The name of the queue
            interface: The interface to add (e.g., 'PJSIP/1000')
            membername: Name for the queue member (defaults to interface if None)
            penalty: Penalty for the member (lower values are called first)
            paused: Whether the member is paused (0=no, 1=yes)
            wrapuptime: Time in seconds after a call before agent can receive another call
            
        Returns:
            bool: True if member was added successfully, False otherwise
        """
        if not self.pool:
            await self.connect()
        
        # Set defaults
        if membername is None:
            # Extract extension from interface (e.g., 'PJSIP/1000' -> '1000')
            parts = interface.split('/')
            if len(parts) > 1:
                membername = parts[1]
            else:
                membername = interface
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Check if queue exists
                    await cursor.execute(
                        "SELECT name FROM queues WHERE name = %s",
                        (queue_name,)
                    )
                    if not await cursor.fetchone():
                        logger.error(f"Queue {queue_name} does not exist")
                        return False
                    
                    # Check if member already exists in the queue
                    await cursor.execute(
                        "SELECT interface FROM queue_members WHERE queue_name = %s AND interface = %s",
                        (queue_name, interface)
                    )
                    if await cursor.fetchone():
                        logger.warning(f"Member {interface} already exists in queue {queue_name}")
                        return False
                    
                    # Add member to queue
                    query = """
                    INSERT INTO queue_members (
                        queue_name, interface, membername, penalty, paused, wrapuptime
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    await cursor.execute(
                        query,
                        (queue_name, interface, membername, penalty, paused, wrapuptime)
                    )
                    
                    logger.info(f"Added member {interface} to queue {queue_name}")
                    
                    # Trigger Asterisk to reload configuration
                    if self.ami_client:
                        try:
                            # Reload queue configuration
                            logger.info(f"Reloading queue configuration after adding member")
                            reload_result = await self.ami_client.manager.send_action({
                                'Action': 'QueueReload',
                                'Queue': queue_name
                            })
                            logger.info(f"Queue configuration reloaded: {reload_result}")
                        except Exception as e:
                            logger.error(f"Failed to reload queue configuration: {e}")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to add member {interface} to queue {queue_name}: {e}")
            return False
    
    async def remove_queue_member(self, queue_name: str, interface: str) -> bool:
        """
        Remove a member from a queue.
        
        Args:
            queue_name: The name of the queue
            interface: The interface to remove (e.g., 'PJSIP/1000')
            
        Returns:
            bool: True if member was removed successfully, False otherwise
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Remove member from queue
                    await cursor.execute(
                        "DELETE FROM queue_members WHERE queue_name = %s AND interface = %s",
                        (queue_name, interface)
                    )
                    
                    if cursor.rowcount == 0:
                        logger.warning(f"Member {interface} not found in queue {queue_name}")
                        return False
                    
                    logger.info(f"Removed member {interface} from queue {queue_name}")
                    
                    # Trigger Asterisk to reload configuration
                    if self.ami_client:
                        try:
                            # Reload queue configuration
                            logger.info(f"Reloading queue configuration after removing member")
                            reload_result = await self.ami_client.manager.send_action({
                                'Action': 'QueueReload',
                                'Queue': queue_name
                            })
                            logger.info(f"Queue configuration reloaded: {reload_result}")
                        except Exception as e:
                            logger.error(f"Failed to reload queue configuration: {e}")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to remove member {interface} from queue {queue_name}: {e}")
            return False
    
    async def list_queue_members(self, queue_name: str) -> List[Dict[str, Any]]:
        """
        List all members in a specific queue.
        
        Args:
            queue_name: The name of the queue
            
        Returns:
            List of dictionaries containing member information
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get all members for the queue
                    await cursor.execute(
                        "SELECT * FROM queue_members WHERE queue_name = %s",
                        (queue_name,)
                    )
                    members = await cursor.fetchall()
                    return members
                    
        except Exception as e:
            logger.error(f"Failed to list members for queue {queue_name}: {e}")
            return []
    
    async def update_queue_member(self, queue_name: str, interface: str, 
                                 updates: Dict[str, Any]) -> bool:
        """
        Update a queue member's settings.
        
        Args:
            queue_name: The name of the queue
            interface: The interface to update (e.g., 'PJSIP/1000')
            updates: Dictionary containing fields to update
            
        Returns:
            bool: True if member was updated successfully, False otherwise
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Build update query dynamically based on provided fields
                    fields = []
                    values = []
                    
                    for key, value in updates.items():
                        if value is not None:
                            fields.append(f"{key} = %s")
                            values.append(value)
                    
                    if not fields:
                        logger.warning(f"No fields to update for member {interface} in queue {queue_name}")
                        return True
                    
                    # Add queue_name and interface to values
                    values.append(queue_name)
                    values.append(interface)
                    
                    # Execute update
                    query = f"UPDATE queue_members SET {', '.join(fields)} WHERE queue_name = %s AND interface = %s"
                    await cursor.execute(query, values)
                    
                    if cursor.rowcount == 0:
                        logger.warning(f"Member {interface} not found in queue {queue_name} or no changes made")
                        return False
                    
                    logger.info(f"Updated member {interface} in queue {queue_name}")
                    
                    # Trigger Asterisk to reload configuration
                    if self.ami_client:
                        try:
                            # Reload queue configuration
                            logger.info(f"Reloading queue configuration after member update")
                            reload_result = await self.ami_client.manager.send_action({
                                'Action': 'QueueReload',
                                'Queue': queue_name
                            })
                            logger.info(f"Queue configuration reloaded: {reload_result}")
                        except Exception as e:
                            logger.error(f"Failed to reload queue configuration: {e}")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to update member {interface} in queue {queue_name}: {e}")
            return False
    
    async def get_queue_status(self, queue_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get real-time status of queues from Asterisk using AMI.
        
        Args:
            queue_name: Optional name of a specific queue to get status for
            
        Returns:
            Dictionary containing queue status information
        """
        if not self.ami_client:
            logger.error("AMI client not set, unable to get queue status")
            return {"error": "AMI client not available"}
        
        try:
            # Prepare QueueStatus action
            action = {'Action': 'QueueStatus'}
            if queue_name:
                action['Queue'] = queue_name
            
            # Send action to Asterisk
            result = await self.ami_client.manager.send_action(action)
            
            # Process and return the result
            return result
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {"error": str(e)}
