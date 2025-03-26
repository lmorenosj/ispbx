#!/usr/bin/env python3
# /home/ubuntu/Documents/ispbx/backend/src/cdr_manager.py

import logging
import aiomysql
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CDRManager:
    """
    Manager for CDR (Call Detail Records) operations using MySQL database.
    
    This class provides methods for retrieving and filtering CDR records
    from the Asterisk CDR database.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 3306,
                 user: str = 'asteriskuser', password: str = 'asteriskpassword',
                 db: str = 'asteriskcdr'):
        """
        Initialize the CDR manager with database connection parameters.
        
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
    
    async def connect(self):
        """Establish connection pool to the MySQL database"""
        if not self.pool:
            try:
                self.pool = await aiomysql.create_pool(**self.db_config)
                logger.info("Connected to CDR MySQL database")
            except Exception as e:
                logger.error(f"Failed to connect to CDR MySQL: {e}")
                raise
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            logger.info("Closed CDR MySQL connection pool")
    
    async def get_cdr_records(self, 
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None,
                             src: Optional[str] = None,
                             dst: Optional[str] = None,
                             disposition: Optional[str] = None,
                             limit: int = 100,
                             offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get CDR records with optional filtering.
        
        Args:
            start_date: Filter by start date (format: YYYY-MM-DD)
            end_date: Filter by end date (format: YYYY-MM-DD)
            src: Filter by source extension
            dst: Filter by destination extension
            disposition: Filter by call disposition (ANSWERED, NO ANSWER, BUSY, FAILED)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of CDR records as dictionaries
        """
        if not self.pool:
            await self.connect()
            
        query = "SELECT * FROM cdr WHERE 1=1"
        params = []
        
        # Apply filters
        if start_date:
            query += " AND DATE(start) >= %s"
            params.append(start_date)
            
        if end_date:
            query += " AND DATE(end) <= %s"
            params.append(end_date)
            
        if src:
            query += " AND src = %s"
            params.append(src)
            
        if dst:
            query += " AND dst = %s"
            params.append(dst)
            
        if disposition:
            query += " AND disposition = %s"
            params.append(disposition)
            
        # Add ordering and pagination
        query += " ORDER BY start DESC LIMIT %s OFFSET %s"
        params.append(limit)
        params.append(offset)
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, params)
                    records = await cur.fetchall()
                    
                    # Convert datetime objects to strings for JSON serialization
                    for record in records:
                        for key, value in record.items():
                            if isinstance(value, datetime):
                                record[key] = value.isoformat()
                    
                    return records
        except Exception as e:
            logger.error(f"Error fetching CDR records: {e}")
            raise
    
    async def get_cdr_stats(self) -> Dict[str, Any]:
        """
        Get CDR statistics.
        
        Returns:
            Dictionary with CDR statistics
        """
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    # Total calls
                    await cur.execute("SELECT COUNT(*) as total FROM cdr")
                    total_result = await cur.fetchone()
                    total_calls = total_result['total'] if total_result else 0
                    
                    # Calls by disposition
                    await cur.execute("SELECT disposition, COUNT(*) as count FROM cdr GROUP BY disposition")
                    disposition_results = await cur.fetchall()
                    disposition_stats = {r['disposition']: r['count'] for r in disposition_results}
                    
                    # Calls today
                    today = datetime.now().strftime('%Y-%m-%d')
                    await cur.execute("SELECT COUNT(*) as count FROM cdr WHERE DATE(start) = %s", (today,))
                    today_result = await cur.fetchone()
                    calls_today = today_result['count'] if today_result else 0
                    
                    # Average call duration (for answered calls)
                    await cur.execute("SELECT AVG(billsec) as avg_duration FROM cdr WHERE disposition = 'ANSWERED'")
                    avg_result = await cur.fetchone()
                    avg_duration = avg_result['avg_duration'] if avg_result and avg_result['avg_duration'] else 0
                    
                    return {
                        "total_calls": total_calls,
                        "disposition_stats": disposition_stats,
                        "calls_today": calls_today,
                        "avg_duration": round(float(avg_duration), 2) if avg_duration else 0
                    }
        except Exception as e:
            logger.error(f"Error fetching CDR statistics: {e}")
            raise
