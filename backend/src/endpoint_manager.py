#!/usr/bin/env python3
# /home/ubuntu/Documents/ispbx/backend/src/endpoint_manager.py

import logging
import aiomysql
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EndpointManager:
    """
    Manager for SIP endpoint operations using MySQL database.
    
    This class provides methods for creating, reading, updating, and deleting
    SIP endpoints in the Asterisk database using MySQL.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 3306,
                 user: str = 'asteriskuser', password: str = 'asteriskpassword',
                 db: str = 'asterisk'):
        """
        Initialize the endpoint manager with database connection parameters.
        
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
                logger.info("Connected to MySQL database")
            except Exception as e:
                logger.error(f"Failed to connect to MySQL: {e}")
                raise
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            logger.info("Disconnected from MySQL database")
    
    async def create_endpoint(self, endpoint_id: str, password: str, name: str = None,
                              context: str = 'from-internal', transport: str = 'transport-udp',
                              codecs: List[str] = None, max_contacts: int = 1) -> bool:
        """
        Create a new SIP endpoint in the database.
        
        Args:
            endpoint_id: The extension number/endpoint ID
            password: Authentication password for the endpoint
            name: Display name for the endpoint (defaults to endpoint_id if None)
            context: Dialplan context for the endpoint
            transport: SIP transport to use
            codecs: List of allowed codecs (defaults to g722)
            max_contacts: Maximum number of contacts for the endpoint
            
        Returns:
            bool: True if endpoint was created successfully, False otherwise
        """
        if not self.pool:
            await self.connect()
        
        # Set defaults
        if name is None:
            name = endpoint_id
        if codecs is None:
            codecs = ['g722']
        
        allow = ','.join(codecs)
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 1. Create AOR (Address of Record) with qualify parameters for device state events
                    await cursor.execute(
                        "INSERT INTO ps_aors (id, max_contacts, qualify_frequency, qualify_timeout) VALUES (%s, %s, %s, %s)",
                        (endpoint_id, max_contacts, 60, 3.0)
                    )
                    
                    # 2. Create Authentication
                    await cursor.execute(
                        "INSERT INTO ps_auths (id, auth_type, password, username) VALUES (%s, %s, %s, %s)",
                        (endpoint_id, 'userpass', password, endpoint_id)
                    )
                    
                    # 3. Create Endpoint with caller ID
                    callerid = f'"{name}" <{endpoint_id}>'
                    await cursor.execute(
                        """INSERT INTO ps_endpoints 
                           (id, transport, aors, auth, context, disallow, allow, direct_media, callerid) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (endpoint_id, transport, endpoint_id, endpoint_id, context, 'all', allow, 'no', callerid)
                    )
                    
                    logger.info(f"Created endpoint {endpoint_id} with name '{name}'")
                    
                    # # Trigger Asterisk to reload configuration and generate events
                    # if self.ami_client:
                    #     try:
                    #         # Use PJSIPReload action to reload PJSIP configuration
                    #         logger.info(f"Reloading PJSIP configuration after endpoint creation")
                    #         reload_result = await self.ami_client.manager.send_action({
                    #             'Action': 'PJSIPReload'
                    #         })
                    #         logger.info(f"PJSIP configuration reloaded: {reload_result}")
                    #         
                    #         # Force a device state refresh for this endpoint
                    #         logger.info(f"Triggering device state refresh for endpoint {endpoint_id}")
                    #         state_result = await self.ami_client.manager.send_action({
                    #             'Action': 'DeviceStateList'
                    #         })
                    #         logger.info(f"Device state refresh triggered")
                    #     except Exception as e:
                    #         logger.error(f"Failed to reload PJSIP configuration: {e}")
                    # else:
                    #     logger.warning("AMI client not set, unable to reload configuration")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to create endpoint {endpoint_id}: {e}")
            return False
    
    async def get_endpoint(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific endpoint.
        
        Args:
            endpoint_id: The extension number/endpoint ID
            
        Returns:
            Dict containing endpoint details or None if not found
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get endpoint details
                    await cursor.execute(
                        "SELECT * FROM ps_endpoints WHERE id = %s",
                        (endpoint_id,)
                    )
                    endpoint = await cursor.fetchone()
                    
                    if not endpoint:
                        return None
                    
                    # Get AOR details
                    await cursor.execute(
                        "SELECT * FROM ps_aors WHERE id = %s",
                        (endpoint_id,)
                    )
                    aor = await cursor.fetchone()
                    
                    # Get auth details
                    await cursor.execute(
                        "SELECT * FROM ps_auths WHERE id = %s",
                        (endpoint_id,)
                    )
                    auth = await cursor.fetchone()
                    
                    # Combine all details
                    result = {
                        'endpoint': endpoint,
                        'aor': aor,
                        'auth': auth
                    }
                    
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to get endpoint {endpoint_id}: {e}")
            return None
    
    async def list_endpoints(self) -> List[Dict[str, Any]]:
        """
        List all endpoints in the database.
        
        Returns:
            List of dictionaries containing basic endpoint information
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Join tables to get comprehensive endpoint information
                    await cursor.execute("""
                        SELECT 
                            e.id, e.context, e.callerid, e.transport,
                            a.max_contacts,
                            u.username, u.auth_type
                        FROM 
                            ps_endpoints e
                        LEFT JOIN 
                            ps_aors a ON e.id = a.id
                        LEFT JOIN 
                            ps_auths u ON e.id = u.id
                    """)
                    
                    endpoints = await cursor.fetchall()
                    return endpoints
                    
        except Exception as e:
            logger.error(f"Failed to list endpoints: {e}")
            return []
    
    async def update_endpoint(self, endpoint_id: str, 
                              updates: Dict[str, Any]) -> bool:
        """
        Update an existing endpoint.
        
        Args:
            endpoint_id: The extension number/endpoint ID
            updates: Dictionary containing fields to update
                     Possible keys:
                     - password: New authentication password
                     - name: New display name
                     - context: New dialplan context
                     - transport: New SIP transport
                     - codecs: New list of allowed codecs
                     - max_contacts: New maximum number of contacts
                     - qualify_frequency: Frequency in seconds to check endpoint status
                     - qualify_timeout: Timeout in seconds for qualify checks
                     
        Returns:
            bool: True if endpoint was updated successfully, False otherwise
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Update AOR if max_contacts or qualify parameters are specified
                    aor_updates = {}
                    aor_params = []
                    
                    if 'max_contacts' in updates:
                        aor_updates['max_contacts'] = '%s'
                        aor_params.append(updates['max_contacts'])
                        
                    if 'qualify_frequency' in updates:
                        aor_updates['qualify_frequency'] = '%s'
                        aor_params.append(updates['qualify_frequency'])
                        
                    if 'qualify_timeout' in updates:
                        aor_updates['qualify_timeout'] = '%s'
                        aor_params.append(updates['qualify_timeout'])
                    
                    if aor_updates:
                        query = "UPDATE ps_aors SET "
                        query += ", ".join([f"{k} = {v}" for k, v in aor_updates.items()])
                        query += " WHERE id = %s"
                        aor_params.append(endpoint_id)
                        await cursor.execute(query, aor_params)
                    
                    # Update auth if password is specified
                    if 'password' in updates:
                        await cursor.execute(
                            "UPDATE ps_auths SET password = %s WHERE id = %s",
                            (updates['password'], endpoint_id)
                        )
                    
                    # Update endpoint fields
                    endpoint_updates = {}
                    
                    if 'context' in updates:
                        endpoint_updates['context'] = updates['context']
                        
                    if 'transport' in updates:
                        endpoint_updates['transport'] = updates['transport']
                        
                    if 'codecs' in updates and isinstance(updates['codecs'], list):
                        endpoint_updates['allow'] = ','.join(updates['codecs'])
                        
                    if 'name' in updates:
                        # Get current callerid to extract number
                        await cursor.execute(
                            "SELECT callerid FROM ps_endpoints WHERE id = %s",
                            (endpoint_id,)
                        )
                        result = await cursor.fetchone()
                        if result and result[0]:
                            # Update callerid with new name but keep same number
                            callerid = f'"{updates["name"]}" <{endpoint_id}>'
                            endpoint_updates['callerid'] = callerid
                    
                    # Execute update if there are endpoint fields to update
                    if endpoint_updates:
                        query = "UPDATE ps_endpoints SET "
                        params = []
                        
                        for i, (key, value) in enumerate(endpoint_updates.items()):
                            query += f"{key} = %s"
                            params.append(value)
                            if i < len(endpoint_updates) - 1:
                                query += ", "
                                
                        query += " WHERE id = %s"
                        params.append(endpoint_id)
                        
                        await cursor.execute(query, params)
                    
                    logger.info(f"Updated endpoint {endpoint_id}")
                    
                    # Trigger Asterisk to reload configuration and generate events
                    if self.ami_client:
                        try:
                            # Use PJSIPReload action to reload PJSIP configuration
                            logger.info(f"Reloading PJSIP configuration after endpoint update")
                            reload_result = await self.ami_client.manager.send_action({
                                'Action': 'PJSIPReload'
                            })
                            logger.info(f"PJSIP configuration reloaded: {reload_result}")
                            
                            # Force a device state refresh for this endpoint
                            logger.info(f"Triggering device state refresh for endpoint {endpoint_id}")
                            state_result = await self.ami_client.manager.send_action({
                                'Action': 'DeviceStateList'
                            })
                            logger.info(f"Device state refresh triggered")
                        except Exception as e:
                            logger.error(f"Failed to reload PJSIP configuration: {e}")
                    else:
                        logger.warning("AMI client not set, unable to reload configuration")
                        
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to update endpoint {endpoint_id}: {e}")
            return False
    
    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """
        Delete an endpoint and its associated records.
        
        Args:
            endpoint_id: The extension number/endpoint ID
            
        Returns:
            bool: True if endpoint was deleted successfully, False otherwise
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Delete from ps_endpoints
                    await cursor.execute(
                        "DELETE FROM ps_endpoints WHERE id = %s",
                        (endpoint_id,)
                    )
                    
                    # Delete from ps_auths
                    await cursor.execute(
                        "DELETE FROM ps_auths WHERE id = %s",
                        (endpoint_id,)
                    )
                    
                    # Delete from ps_aors
                    await cursor.execute(
                        "DELETE FROM ps_aors WHERE id = %s",
                        (endpoint_id,)
                    )
                    
                    logger.info(f"Deleted endpoint {endpoint_id}")
                    
                    # Trigger Asterisk to reload configuration and generate events
                    if self.ami_client:
                        try:
                            # Use PJSIPReload action to reload PJSIP configuration
                            logger.info(f"Reloading PJSIP configuration after endpoint deletion")
                            reload_result = await self.ami_client.manager.send_action({
                                'Action': 'PJSIPReload'
                            })
                            logger.info(f"PJSIP configuration reloaded: {reload_result}")
                            
                            # Force a device state refresh
                            logger.info(f"Triggering device state refresh after deletion")
                            state_result = await self.ami_client.manager.send_action({
                                'Action': 'DeviceStateList'
                            })
                            logger.info(f"Device state refresh triggered")
                        except Exception as e:
                            logger.error(f"Failed to reload PJSIP configuration: {e}")
                    else:
                        logger.warning("AMI client not set, unable to reload configuration")
                        
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to delete endpoint {endpoint_id}: {e}")
            return False
