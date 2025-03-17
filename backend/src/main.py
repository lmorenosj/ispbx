#app.py
from email import message
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        logger.info(f"Request: endpoint=/endpoints/{extension if extension else ''}, method=GET, params={{'extension': extension}}, status_code=200")
        return response
    except HTTPException:
        raise
    except Exception as e:
        # Log error for the specific endpoint or general endpoint retrieval
        logger.error(f"Error getting PJSIP details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get endpoint details")


@app.get("/api/endpoints/{extension}/config")
async def get_endpoint_config(extension: str):
    """Get the complete configuration for a specific endpoint
    
    Returns the full configuration of an endpoint from pjsip.conf,
    including its endpoint, auth, and aor sections.
    """
    try:
        # Get endpoint configuration
        logger.info(f"Request: endpoint=/endpoints/{extension}/config, method=GET")
        result = await ami_client.get_endpoint_config(extension)
        
        # Check result
        if result['status'] == 'error':
            if 'not found' in result['message']:
                raise HTTPException(status_code=404, detail=result['message'])
            else:
                raise HTTPException(status_code=400, detail=result['message'])
        
        # Log the request
        logger.info(f"Request: endpoint=/endpoints/{extension}/config, method=GET, status_code=200")
        
        # Return success response with configuration
        return {
            "status": "success",
            "message": result['message'],
            "config": result['config']
        }
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        logger.error(f"Error getting endpoint configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to get endpoint configuration")




@app.put("/api/endpoints/{extension}")
async def update_endpoint(extension: str, endpoint_data: dict):
    """Update an existing PJSIP endpoint configuration
    
    Optional fields in endpoint_data:
    - name: The caller ID name
    - password: Authentication password
    - context: Dialplan context for incoming calls
    - transport: SIP transport
    - allow: Allowed codecs
    - disallow: Disallowed codecs
    """
    try:
        # Update the endpoint
        logger.info(f"Updating endpoint {extension} with data: {endpoint_data}")
        result = await ami_client.update_endpoint(extension, endpoint_data)
        
        # Check result
        if result['status'] == 'error':
            if 'not found' in result['message']:
                raise HTTPException(status_code=404, message=result['message'])
            else:
                raise HTTPException(status_code=400, message=result['message'])
        
        # Log the request
        logger.info(f"Request: endpoint=/endpoints/{extension}, method=PUT, data={endpoint_data}, status_code=200")
        
        # Return success response
        return {
            "status": "success",
            "message": result['message'],
            "extension": result['extension']
        }
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        logger.error(f"Error updating endpoint: {e}")
        raise HTTPException(status_code=500, message="Failed to update endpoint")


@app.post("/api/endpoints", status_code=201)
async def add_endpoint(endpoint_data: dict):
    """Add a new PJSIP endpoint configuration
    
    Required fields in endpoint_data:
    - extension: The endpoint extension number
    - name: The caller ID name
    - password: Authentication password
    
    Optional fields in endpoint_data:
    - context: Dialplan context for incoming calls (default: from-internal)
    - transport: SIP transport (default: transport-udp)
    - allow: Allowed codecs (default: ulaw,alaw)
    - disallow: Disallowed codecs (default: all)
    """
    try:
        # Add the endpoint
        result = await ami_client.add_endpoint(endpoint_data)
        
        # Check result
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        
        # Log the request
        logger.info(f"Request: endpoint=/endpoints, method=POST, data={endpoint_data}, status_code=201")
        
        # Return success response
        return {
            "status": "success",
            "message": result['message'],
            "extension": result['extension']
        }
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        logger.error(f"Error adding endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to add endpoint")


@app.delete("/api/endpoints/{extension}")
async def delete_endpoint(extension: str):
    """Delete a PJSIP endpoint configuration"""
    try:
        # Delete the endpoint
        result = await ami_client.delete_endpoint(extension)
        
        # Check result
        if result['status'] == 'error':
            if 'not found' in result['message']:
                raise HTTPException(status_code=404, detail=result['message'])
            else:
                raise HTTPException(status_code=400, detail=result['message'])
        
        # Log the request
        logger.info(f"Request: endpoint=/endpoints/{extension}, method=DELETE, status_code=200")
        
        # Return success response
        return {
            "status": "success",
            "message": result['message']
        }
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        logger.error(f"Error deleting endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete endpoint")



# Expose socket_app for uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "main:socket_app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )