import socketio
import logging
import time
import threading
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Connection configuration
SOCKETIO_SERVER = 'http://127.0.0.1:8000'

# Create Socket.IO client
sio = socketio.Client(
    logger=True,
    reconnection=True
)

@sio.event
def connect():
    print("Connected to Socket.IO server!")
    logger.info("Connected to Socket.IO server")

@sio.event
def connect_error(data):
    print("Connection Error:", data)
    logger.error(f"Connection error: {data}")

@sio.event
def disconnect():
    print("Disconnected from Socket.IO server")
    logger.warning("Disconnected from Socket.IO server")

@sio.event
def message(data):
    print(f"Message received: {data}")
    logger.info(f"Message received: {data}")

@sio.event
def catch_all(event, data):
    print(f"Event received: {event} with data: {data}")
    logger.info(f"Event received: {event} with data: {data}")
    logger.debug(f"Event details - name: {event}, data type: {type(data)}, content: {data}")


def main():
    try:
        print("Attempting to connect to Socket.IO server...")
        logger.info(f"Connecting to Socket.IO server at {SOCKETIO_SERVER}")
        
        # Connect to the Socket.IO server
        sio.connect(SOCKETIO_SERVER)
        
        # Wait for incoming Socket.IO events
        logger.info("Connection successful, waiting for events")
        sio.wait()
        
    except socketio.exceptions.ConnectionError as e:
        logger.error(f"Failed to connect to server: {e}")
        print(f"Connection Error: {e}")
        
    except Exception as e:
        print(f"Unexpected Error: {e}")
        logger.error(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()