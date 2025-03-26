#app.py
import os
import socketio
import uvicorn
from fastapi import FastAPI, Body, Query
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
from cdr_manager import CDRManager
from queue_manager import QueueManager
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

# Pydantic models for queue operations
class QueueCreate(BaseModel):
    queue_name: str  # Required
    strategy: str = "ringall"
    timeout: int = 15
    musiconhold: str = "default"
    announce: Optional[str] = None
    context: str = "from-queue"
    maxlen: int = 0
    servicelevel: int = 60
    wrapuptime: int = 0

class QueueUpdate(BaseModel):
    strategy: Optional[str] = None
    timeout: Optional[int] = None
    musiconhold: Optional[str] = None
    announce: Optional[str] = None
    context: Optional[str] = None
    maxlen: Optional[int] = None
    servicelevel: Optional[int] = None
    wrapuptime: Optional[int] = None

class QueueMemberAdd(BaseModel):
    interface: str  # Required (e.g., 'PJSIP/1000')
    membername: Optional[str] = None
    penalty: int = 0
    paused: int = 0
    wrapuptime: Optional[int] = None

class QueueMemberUpdate(BaseModel):
    membername: Optional[str] = None
    penalty: Optional[int] = None
    paused: Optional[int] = None
    wrapuptime: Optional[int] = None

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

# Initialize CDR manager
cdr_manager = CDRManager(
    host=os.getenv('MYSQL_HOST', 'localhost'),
    port=int(os.getenv('MYSQL_PORT', '3306')),
    user=os.getenv('MYSQL_USER', 'asteriskuser'),
    password=os.getenv('MYSQL_PASSWORD', 'asteriskpassword'),
    db=os.getenv('CDR_MYSQL_DATABASE', 'asterisk')
)

# Initialize queue manager
queue_manager = QueueManager(
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
        
        # Connect to CDR MySQL database
        logger.info("Connecting to CDR MySQL database...")
        await cdr_manager.connect()
        logger.info("CDR MySQL connection established successfully")
        
        # Set AMI client in endpoint manager to enable configuration reloads
        endpoint_manager.ami_client = ami_client
        logger.info("AMI client set in endpoint manager")
        
        # Set AMI client in queue manager to enable configuration reloads
        queue_manager.ami_client = ami_client
        logger.info("AMI client set in queue manager")
        
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
            
            # Close MySQL connections
            logger.info("Closing MySQL connections...")
            await endpoint_manager.close()
            await queue_manager.close()
            logger.info("MySQL connections closed successfully")
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

# API root endpoint

# Mount Socket.IO on the FastAPI app
socket_app = socketio.ASGIApp(sio, app)



@app.get("/")
async def root():
    # API root endpoint
    return {"message": "ISPBX API is running"}

@app.get("/api")
async def api_root():
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

# Queue API Routes
@app.post("/api/queues", status_code=201)
async def create_queue(queue: QueueCreate):
    """Create a new queue"""
    try:
        logger.info(f"Creating queue {queue.queue_name}, payload={queue}")
        
        # Check if queue already exists
        existing = await queue_manager.get_queue(queue.queue_name)
        if existing:
            raise HTTPException(status_code=409, detail=f"Queue {queue.queue_name} already exists")
        
        # Create queue
        success = await queue_manager.create_queue(
            queue_name=queue.queue_name,
            strategy=queue.strategy,
            timeout=queue.timeout,
            musiconhold=queue.musiconhold,
            announce=queue.announce,
            context=queue.context,
            maxlen=queue.maxlen,
            servicelevel=queue.servicelevel,
            wrapuptime=queue.wrapuptime
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create queue")
        
        # Get the created queue
        created_queue = await queue_manager.get_queue(queue.queue_name)
        
        return {
            "status": "success",
            "message": f"Queue {queue.queue_name} created successfully",
            "queue": created_queue
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating queue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create queue: {str(e)}")

@app.get("/api/queues")
async def list_queues():
    """List all queues"""
    try:
        queues = await queue_manager.list_queues()
        return {
            "status": "success",
            "queues": queues
        }
    except Exception as e:
        logger.error(f"Error listing queues: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list queues: {str(e)}")

@app.get("/api/queues/{queue_name}")
async def get_queue(queue_name: str):
    """Get details for a specific queue"""
    try:
        queue = await queue_manager.get_queue(queue_name)
        if not queue:
            raise HTTPException(status_code=404, detail=f"Queue {queue_name} not found")
        
        return {
            "status": "success",
            "queue": queue
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue: {str(e)}")

@app.put("/api/queues/{queue_name}")
async def update_queue(queue_name: str, updates: QueueUpdate):
    """Update an existing queue"""
    try:
        # Check if queue exists
        existing = await queue_manager.get_queue(queue_name)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Queue {queue_name} not found")
        
        # Convert Pydantic model to dict, excluding None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            return {
                "status": "success",
                "message": "No updates provided"
            }
        
        # Update queue
        success = await queue_manager.update_queue(queue_name, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update queue")
        
        # Get the updated queue
        updated_queue = await queue_manager.get_queue(queue_name)
        
        return {
            "status": "success",
            "message": f"Queue {queue_name} updated successfully",
            "queue": updated_queue
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update queue: {str(e)}")

@app.delete("/api/queues/{queue_name}")
async def delete_queue(queue_name: str):
    """Delete a queue"""
    try:
        # Check if queue exists
        existing = await queue_manager.get_queue(queue_name)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Queue {queue_name} not found")
        
        # Delete queue
        success = await queue_manager.delete_queue(queue_name)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete queue")
        
        return {
            "status": "success",
            "message": f"Queue {queue_name} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete queue: {str(e)}")

@app.post("/api/queues/{queue_name}/members")
async def add_queue_member(queue_name: str, member: QueueMemberAdd):
    """Add a member to a queue"""
    try:
        # Check if queue exists
        existing = await queue_manager.get_queue(queue_name)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Queue {queue_name} not found")
        
        # Add member to queue
        success = await queue_manager.add_queue_member(
            queue_name=queue_name,
            interface=member.interface,
            membername=member.membername,
            penalty=member.penalty,
            paused=member.paused,
            wrapuptime=member.wrapuptime
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add member to queue")
        
        # Get updated queue members
        members = await queue_manager.list_queue_members(queue_name)
        
        return {
            "status": "success",
            "message": f"Member {member.interface} added to queue {queue_name}",
            "members": members
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding member to queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add member to queue: {str(e)}")

@app.get("/api/queues/{queue_name}/members")
async def list_queue_members(queue_name: str):
    """List all members in a queue"""
    try:
        # Check if queue exists
        existing = await queue_manager.get_queue(queue_name)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Queue {queue_name} not found")
        
        # Get queue members
        members = await queue_manager.list_queue_members(queue_name)
        
        return {
            "status": "success",
            "members": members
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing members for queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list queue members: {str(e)}")

@app.put("/api/queues/{queue_name}/members/{interface}")
async def update_queue_member(queue_name: str, interface: str, updates: QueueMemberUpdate):
    """Update a queue member"""
    try:
        # Format interface to ensure it's in the correct format
        if not interface.startswith("PJSIP/"):
            interface = f"PJSIP/{interface}"
        
        # Convert Pydantic model to dict, excluding None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            return {
                "status": "success",
                "message": "No updates provided"
            }
        
        # Update queue member
        success = await queue_manager.update_queue_member(queue_name, interface, update_data)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Member {interface} not found in queue {queue_name}")
        
        # Get updated queue members
        members = await queue_manager.list_queue_members(queue_name)
        
        return {
            "status": "success",
            "message": f"Member {interface} updated in queue {queue_name}",
            "members": members
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating member {interface} in queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update queue member: {str(e)}")

@app.delete("/api/queues/{queue_name}/members/{interface}")
async def remove_queue_member(queue_name: str, interface: str):
    """Remove a member from a queue"""
    try:
        # Format interface to ensure it's in the correct format
        if not interface.startswith("PJSIP/"):
            interface = f"PJSIP/{interface}"
        
        # Remove member from queue
        success = await queue_manager.remove_queue_member(queue_name, interface)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Member {interface} not found in queue {queue_name}")
        
        return {
            "status": "success",
            "message": f"Member {interface} removed from queue {queue_name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member {interface} from queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove queue member: {str(e)}")

@app.get("/api/queues/status")
@app.get("/api/queues/{queue_name}/status")
async def get_queue_status(queue_name: Optional[str] = None):
    """Get real-time status of queues from Asterisk"""
    try:
        status = await queue_manager.get_queue_status(queue_name)
        
        return {
            "status": "success",
            "queue_status": status
        }
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")

# CDR API Routes
@app.get("/api/cdr")
async def get_cdr_records(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    src: Optional[str] = Query(None, description="Source extension"),
    dst: Optional[str] = Query(None, description="Destination extension"),
    disposition: Optional[str] = Query(None, description="Call disposition (ANSWERED, NO ANSWER, BUSY, FAILED)"),
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Number of records to skip")
):
    """Get CDR records with optional filtering"""
    try:
        logger.info(f"Fetching CDR records with filters: start_date={start_date}, end_date={end_date}, src={src}, dst={dst}, disposition={disposition}")
        records = await cdr_manager.get_cdr_records(
            start_date=start_date,
            end_date=end_date,
            src=src,
            dst=dst,
            disposition=disposition,
            limit=limit,
            offset=offset
        )
        
        return {
            "status": "success",
            "count": len(records),
            "records": records
        }
    except Exception as e:
        logger.error(f"Error fetching CDR records: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch CDR records: {str(e)}")

@app.get("/api/cdr/stats")
async def get_cdr_stats():
    """Get CDR statistics"""
    try:
        logger.info("Fetching CDR statistics")
        stats = await cdr_manager.get_cdr_stats()
        
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error fetching CDR statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch CDR statistics: {str(e)}")

# Expose socket_app for uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "main:socket_app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )