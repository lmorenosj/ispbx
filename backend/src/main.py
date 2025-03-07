#app.py
import os
import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from fastapi import HTTPException
import logging
from contextlib import asynccontextmanager
from client import AmiClient
from events import sio, broadcast_event  # Import from events.py

# Configure logging
logging.basicConfig(level=logging.INFO)
api_logger = logging.getLogger("api_logger")
logger = logging.getLogger(__name__)


# Initialize AMI client with the broadcast_event
ami_client = AmiClient(
    event_callback=broadcast_event,
    host=os.getenv('ASTERISK_HOST', '127.0.0.1'),
    port=int(os.getenv('ASTERISK_AMI_PORT', '5038')),
    username=os.getenv('ASTERISK_AMI_USER', 'admin'),
    password=os.getenv('ASTERISK_AMI_PASSWORD', 'admin')
)

# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting application, connecting to AMI...")
        await ami_client.connect()
        logger.info("AMI connection established successfully")
        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    finally:
        try:
            logger.info("Shutting down, closing AMI connection...")
            await ami_client.close()
            logger.info("AMI connection closed successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="ISPBX Manager",
    description="Real-time PBX Management API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    logger.info(f"SocketIO client connected: {sid}")
    pass

@sio.event
async def disconnect(sid):
    logger.info(f"SocketIO client disconnected: {sid}")
    pass

# Mount Socket.IO on the FastAPI app
socket_app = socketio.ASGIApp(sio, app)



@app.get("/")
async def root():
    return {
        "message": "ISPBX Manager API",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/api/endpoints")
@app.get("/api/endpoints/{extension}")
async def get_pjsip_details(extension: Optional[str] = None):
    """Get details for all or a specific PJSIP endpoint"""
    try:
        # Get endpoint details, passing None if no extension is provided
        endpoint_details = await ami_client.get_endpoint_details(extension)
        
        # If an extension is specified and not found, raise 404
        if extension and not endpoint_details.get('details'):
            raise HTTPException(status_code=404, detail=f"Extension {extension} not found")
        
        # Prepare response
        response = {
            "status": "success",
            "endpoints": endpoint_details.get('endpoints', []),
            "details": endpoint_details.get('details', {})
        }
        
        # Log the request
        api_logger.info(f"Request: endpoint=/endpoints/{extension if extension else ''}, method=GET, params={{'extension': extension}}, status_code=200")
        return response
    except HTTPException:
        raise
    except Exception as e:
        # Log error for the specific endpoint or general endpoint retrieval
        api_logger.error(f"Error getting PJSIP details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get endpoint details")

# Expose socket_app for uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "main:socket_app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )