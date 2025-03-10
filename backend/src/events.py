# /home/ubuntu/Documents/ispbx/backend/src/events.py

import socketio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode='asgi', 
    cors_allowed_origins=['*']
)

async def broadcast_event(event_type: str, event_data: dict):
    """Broadcast an event to all connected Socket.IO clients"""
    
    try:
        logger.info(f"Broadcasting event: {event_type}")
        await sio.emit(event_type, {"data": event_data})
    except Exception:
        pass