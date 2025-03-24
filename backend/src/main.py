#app.py
from email import message
import os
import socketio
import uvicorn
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional, List
from fastapi import HTTPException
import logging
from contextlib import asynccontextmanager
from client import AmiClient
from events import sio, broadcast_event  # Import from events.py
from endpoint_manager import EndpointManager
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Pydantic models for endpoint operations
class EndpointCreate(BaseModel):
    endpoint_id: str  # Required
    password: str     # Required
    name: Optional[str] = None
    context: str = "from-internal"
    transport: str = "transport-udp"
    codecs: List[str] = ["g722"]
    max_contacts: int = 1

class EndpointUpdate(BaseModel):
    password: Optional[str] = None
    name: Optional[str] = None
    context: Optional[str] = None
    transport: Optional[str] = None
    codecs: Optional[List[str]] = None
    max_contacts: Optional[int] = None

# Initialize AMI client with the broadcast_event
ami_client = AmiClient(
    event_callback=broadcast_event,
    host=os.getenv('ASTERISK_HOST', '127.0.0.1'),
    port=int(os.getenv('ASTERISK_AMI_PORT', '5038')),
    username=os.getenv('ASTERISK_AMI_USER', 'admin'),
    password=os.getenv('ASTERISK_AMI_PASSWORD', 'admin')
)

# Initialize endpoint manager
endpoint_manager = EndpointManager(
    host=os.getenv('MYSQL_HOST', 'localhost'),
    port=int(os.getenv('MYSQL_PORT', '3306')),
    user=os.getenv('MYSQL_USER', 'asteriskuser'),
    password=os.getenv('MYSQL_PASSWORD', 'asteriskpassword'),
    db=os.getenv('MYSQL_DATABASE', 'asterisk')
)

# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting application, connecting to AMI...")
        await ami_client.connect()
        logger.info("AMI connection established successfully")
        
        # Connect to MySQL database
        logger.info("Connecting to MySQL database...")
        await endpoint_manager.connect()
        logger.info("MySQL connection established successfully")
        
        # Set AMI client in endpoint manager to enable configuration reloads
        endpoint_manager.ami_client = ami_client
        logger.info("AMI client set in endpoint manager")
        
        # Test AMI event handling
        logger.info("Testing AMI event handling...")
        test_event = {
            "Event": "TestEvent",
            "Message": "This is a test event to verify event handling"
        }
        await broadcast_event("TestEvent", test_event)
        logger.info("Test event broadcast completed")
        
        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    finally:
        try:
            logger.info("Shutting down, closing AMI connection...")
            await ami_client.close()
            logger.info("AMI connection closed successfully")
            
            # Close MySQL connection
            logger.info("Closing MySQL connection...")
            await endpoint_manager.close()
            logger.info("MySQL connection closed successfully")
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

""" # Mount static files directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Favicon route
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(static_dir, 'img', 'favicon.ico')
    return FileResponse(favicon_path) """

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
        logger.info(f"Request: endpoint=/endpoints/{extension if extension else ''}, method=GET, params={{'extension': extension}}, status_code=200")
        return response
    except HTTPException:
        raise
    except Exception as e:
        # Log error for the specific endpoint or general endpoint retrieval
        logger.error(f"Error getting PJSIP details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get endpoint details")

# Endpoint Management API Routes
@app.post("/api/endpoints", status_code=201)
async def create_endpoint(endpoint: EndpointCreate):
    """Create a new SIP endpoint"""
    try:
        # Check if endpoint already exists
        logger.info(f"Creating endpoint {endpoint.endpoint_id}, payload={endpoint}")
        existing = await endpoint_manager.get_endpoint(endpoint.endpoint_id)
        if existing:
            raise HTTPException(status_code=409, detail=f"Endpoint {endpoint.endpoint_id} already exists")
        
        # Create the endpoint
        success = await endpoint_manager.create_endpoint(
            endpoint_id=endpoint.endpoint_id,
            password=endpoint.password,
            name=endpoint.name,
            context=endpoint.context,
            transport=endpoint.transport,
            codecs=endpoint.codecs,
            max_contacts=endpoint.max_contacts
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create endpoint")
        
        # Reload Asterisk to apply changes
        await ami_client.manager.send_action({'Action': 'PJSIPReload'})
        
        logger.info(f"Created endpoint {endpoint.endpoint_id}")
        return {"status": "success", "message": f"Endpoint {endpoint.endpoint_id} created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create endpoint: {str(e)}")

@app.get("/api/endpoints/db")
async def list_db_endpoints():
    """List all endpoints from the database"""
    try:
        endpoints = await endpoint_manager.list_endpoints()
        return {"status": "success", "endpoints": endpoints}
    except Exception as e:
        logger.error(f"Error listing endpoints: {e}")
        raise HTTPException(status_code=500, detail="Failed to list endpoints")

@app.get("/api/endpoints/db/{endpoint_id}")
async def get_db_endpoint(endpoint_id: str):
    """Get details for a specific endpoint from the database"""
    try:
        endpoint = await endpoint_manager.get_endpoint(endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_id} not found")
        
        return {"status": "success", "endpoint": endpoint}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get endpoint details")

@app.put("/api/endpoints/{endpoint_id}")
async def update_endpoint(endpoint_id: str, updates: EndpointUpdate):
    """Update an existing SIP endpoint"""
    try:
        # Check if endpoint exists
        existing = await endpoint_manager.get_endpoint(endpoint_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_id} not found")
        
        # Convert Pydantic model to dict, excluding None values
        updates_dict = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not updates_dict:
            return {"status": "success", "message": "No updates provided"}
        
        # Update the endpoint
        success = await endpoint_manager.update_endpoint(endpoint_id, updates_dict)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update endpoint")
        
        # Reload Asterisk to apply changes
        await ami_client.manager.send_action({'Action': 'PJSIPReload'})
        
        logger.info(f"Updated endpoint {endpoint_id}")
        return {"status": "success", "message": f"Endpoint {endpoint_id} updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update endpoint: {str(e)}")

@app.delete("/api/endpoints/{endpoint_id}")
async def delete_endpoint(endpoint_id: str):
    """Delete a SIP endpoint"""
    try:
        # Check if endpoint exists
        existing = await endpoint_manager.get_endpoint(endpoint_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_id} not found")
        
        # Delete the endpoint
        success = await endpoint_manager.delete_endpoint(endpoint_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete endpoint")
        
        # Reload Asterisk to apply changes
        await ami_client.manager.send_action({'Action': 'PJSIPReload'})
        
        logger.info(f"Deleted endpoint {endpoint_id}")
        return {"status": "success", "message": f"Endpoint {endpoint_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting endpoint {endpoint_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete endpoint: {str(e)}")

# Expose socket_app for uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "main:socket_app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )