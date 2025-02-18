import os
import ast
import json
import logging
import socketio
import configparser
from typing import Dict, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from logger import api_logger
from ami import AmiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

# Initialize Socket.IO
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=['*'],
    logger=False,
    engineio_logger=False
)

# Mount Socket.IO and configure CORS
app.mount('/socket.io', socketio.ASGIApp(sio))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Constants
PJSIP_CONF_PATH = "/etc/asterisk/pjsip.conf"
PJSIP_CONFIG_INI_PATH = "src/config/pjsip_config.ini"
PJSIP_DETAIL_INI_PATH = "src/config/pjsip_detail.ini"

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

async def broadcast_event(event_type: str, event_data: Dict):
    """Broadcast an event to all connected Socket.IO clients"""
    await sio.emit(event_type, {"data": event_data})

# Initialize AMI client
ami_client = AmiClient(
    event_callback=broadcast_event,
    host=os.getenv('ASTERISK_HOST', '127.0.0.1'),
    port=int(os.getenv('ASTERISK_AMI_PORT', '5038')),
    username=os.getenv('ASTERISK_AMI_USER', 'admin'),
    password=os.getenv('ASTERISK_AMI_PASSWORD', 'admin')
)

# Lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to AMI
    await ami_client.connect()
    yield
    # Shutdown: close AMI connection
    await ami_client.close()

# Update FastAPI app with lifespan
app = FastAPI(
    title="ISPBX Manager",
    version="1.0.0",
    lifespan=lifespan
)



def read_pjsip_conf() -> Dict:
    """Read and parse the pjsip.conf file"""
    if not os.path.exists(PJSIP_CONF_PATH):
        raise FileNotFoundError(f"PJSIP configuration file not found at {PJSIP_CONF_PATH}")
    
    try:
        config_parser = configparser.ConfigParser(allow_no_value=True, comment_prefixes=(';',))
        config_parser.read(PJSIP_CONF_PATH)
        return {section: dict(config_parser[section]) for section in config_parser.sections()}
    except Exception as e:
        logger.error(f"Error reading PJSIP configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Error reading PJSIP configuration")

@app.get("/")
async def root():
    return {"message": "ISPBX Manager API"}


@app.get("/endpoints/{extension}/config")
async def get_pjsip_extension_config(extension: str):
    """Get filtered PJSIP configuration for a specific extension"""
    try:
        # Get allowed parameters from config
        config_parser = configparser.ConfigParser()
        config_parser.read(PJSIP_CONFIG_INI_PATH)
        allowed_params = {param for section in config_parser.sections()
                         for param, value in config_parser[section].items()
                         if value.lower() == 'true'}

        # Get and filter extension config
        raw_config = read_pjsip_conf()
        if extension not in raw_config:
            raise HTTPException(status_code=404, detail=f"Extension {extension} not found")

        config = {k: v for k, v in raw_config[extension].items() if k in allowed_params}
        if not config:
            raise HTTPException(status_code=404, detail=f"No allowed parameters found for {extension}")

        return {"status": "success", "extension": extension, "config": config}

    except HTTPException:
        raise
    except Exception as e:
        api_logger.log_request(
            endpoint=f"/endpoints/{extension}/config",
            method="GET",
            params={"extension": extension},
            status_code=500,
            error=e
        )
        logger.error(f"Error reading PJSIP config: {e}")
        raise HTTPException(status_code=500, detail="Failed to read PJSIP configuration")

@app.get("/endpoints")
async def get_pjsip_details():
    """Get details for all PJSIP endpoints"""
    try:
        endpoint_details = await ami_client.get_endpoint_details(None)
        response = {"status": "success", "endpoints": endpoint_details.get('endpoints', [])}
        api_logger.log_request(endpoint="/endpoints", method="GET", params={}, status_code=200)
        return response
    except Exception as e:
        logger.error(f"Error getting PJSIP details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get endpoint details")


@app.get("/endpoints/{extension}")
async def get_pjsip_details(extension: str):
    """Get details for a specific PJSIP endpoint"""
    try:
        endpoint_details = await ami_client.get_endpoint_details(extension)
        if not endpoint_details.get('details'):
            raise HTTPException(status_code=404, detail=f"Extension {extension} not found")
            
        response = {
            "status": "success",
            "extension": extension,
            "details": endpoint_details.get('details', {})
        }
        api_logger.log_request(
            endpoint=f"/endpoints/{extension}",
            method="GET",
            params={"extension": extension},
            status_code=200
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        api_logger.log_request(
            endpoint=f"/endpoints/{extension}",
            method="GET",
            params={"extension": extension},
            status_code=500,
            error=e
        )
        logger.error(f"Error getting PJSIP details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get endpoint details")

async def get_pjsip_config(extension: str = None) -> Dict:
    """Get PJSIP configuration for an extension or all endpoints"""
    try:
        config = read_pjsip_conf()
        if not extension:
            return {"status": "success", "endpoints": config}
            
        if extension not in config:
            raise HTTPException(status_code=404, detail=f"Extension {extension} not found")
            
        return {
            "status": "success",
            "extension": extension,
            "config": {
                "type": "endpoint",
                "max_contacts": config[extension].get("max_contacts", "1"),
                "callerid": config[extension].get("callerid", f"{extension} <{extension}>")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading PJSIP config: {e}")
        raise HTTPException(status_code=500, detail="Failed to read PJSIP configuration")

@app.get("/api/calls/active")
async def get_active_calls():
    """Get information about all active calls"""
    try:
        calls = await ami_client.get_active_calls()
        return {"status": "success", "calls": calls}
    except Exception as e:
        logger.error(f"Error getting active calls: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active calls")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
