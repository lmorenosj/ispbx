#!/usr/bin/env python3
import asyncio
import os
import sys
import logging
import json
from datetime import datetime
from panoramisk import Manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Custom event handler that prints all events
async def print_event(manager, event):
    event_type = event.get('Event')
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] Received event: {event_type}")
    print(json.dumps(dict(event), indent=2))
    print("-" * 50)

async def listen_for_events():
    # Initialize AMI client directly using panoramisk
    manager = Manager(
        host='127.0.0.1',
        port=5038,
        username='admin',
        secret='admin',  # Panoramisk uses 'secret' instead of 'password'
        ping_delay=10  # Seconds between ping
    )
    
    try:
        # Connect to AMI
        logger.info("Connecting to AMI...")
        await manager.connect()
        logger.info("Connected to AMI! Listening for events...")
        
        # Register our custom event handler for all events
        manager.register_event('*', print_event)
        
        # Keep the script running to receive events
        print("Listening for AMI events... Press Ctrl+C to stop")
        print("Try making changes to endpoints or making a call to generate events")
        while True:
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("Stopping event listener...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Clean up
        manager.close()
        logger.info("AMI connection closed")

if __name__ == "__main__":
    asyncio.run(listen_for_events())
