# /home/ubuntu/Documents/ispbx/backend/src/events.py

import socketio

sio = socketio.AsyncServer(
    async_mode='asgi', 
    cors_allowed_origins=['*']
)

async def broadcast_event(event_type: str, event_data: dict):
    """Broadcast an event to all connected Socket.IO clients"""
    
    try:
        await sio.emit(event_type, {"data": event_data})
    except Exception:
        pass