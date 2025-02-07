from fastapi import FastAPI, HTTPException
import os
from typing import Dict, Optional
import logging
from datetime import datetime
from ami_client import AmiClient
from config.pjsip_config import EXTENSION_PARAMS
from config import pjsip_status_params

app = FastAPI(title="ISPBX Manager", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PJSIP_CONF_PATH = "/etc/asterisk/pjsip.conf"

# Initialize AMI client
ami_client = AmiClient(
    host=os.getenv('ASTERISK_HOST', '127.0.0.1'),
    port=int(os.getenv('ASTERISK_AMI_PORT', '5038')),
    username=os.getenv('ASTERISK_AMI_USER', 'admin'),
    password=os.getenv('ASTERISK_AMI_PASSWORD', 'admin')
)

@app.on_event("startup")
async def startup_event():
    """Connect to AMI when application starts"""
    await ami_client.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Close AMI connection when application shuts down"""
    await ami_client.close()



def read_pjsip_conf() -> Dict:
    """
    Read and parse the pjsip.conf file
    """
    if not os.path.exists(PJSIP_CONF_PATH):
        raise FileNotFoundError(f"PJSIP configuration file not found at {PJSIP_CONF_PATH}")
    
    config = {}
    current_section = None
    
    try:
        with open(PJSIP_CONF_PATH, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith(';'):
                    continue
                    
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    if current_section not in config:
                        config[current_section] = {}
                elif current_section and '=' in line:
                    key, value = [x.strip() for x in line.split('=', 1)]
                    config[current_section][key] = value
                    
        return config
    except Exception as e:
        logger.error(f"Error reading PJSIP configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Error reading PJSIP configuration")

@app.get("/")
async def root():
    return {"message": "ISPBX Manager API"}

@app.get("/endpoints")
@app.get("/endpoints/{extension}")
async def get_pjsip_details(extension: str = None):
    """
    Get PJSIP endpoint details, optionally filtered by extension
    """
    try:
        endpoint_details = await ami_client.get_endpoint_details(extension)
        filtered_response = {}
        
        if extension is None:
            return {
                "status": "success",
                "endpoints": endpoint_details.get('endpoints', [])
            }
        
        if 'response' in endpoint_details:
            for event in endpoint_details['response']:
                event_type = event.get('Event')
                
                # Skip non-event items and completion events
                if not event_type or event_type in pjsip_status_params.SKIP_EVENTS or event.get('Response') == 'Success':
                    continue
                
                # Filter the event based on configured parameters
                filtered_event = pjsip_status_params.filter_event(event, event_type)
                if filtered_event:
                    # Convert event type to lowercase for response key
                    key = event_type.replace('Detail', '').lower()
                    filtered_response[key] = filtered_event
        
        return {
            "status": "success",
            "extension": extension,
            "details": filtered_response
        }
    except Exception as e:
        logger.error(f"Error getting PJSIP details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/endpoints/{extension}/config")
async def get_pjsip_extension_config(extension: str):
    """
    Get PJSIP configuration for a specific extension from pjsip.conf
    Returns configuration in JSON format with all parameters in a single section
    """
    try:
        raw_config = read_pjsip_conf()
        config = {}
        
        if extension in raw_config:
            section_data = raw_config[extension]
            
            # Add all relevant parameters to config
            for key, value in section_data.items():
                if key in EXTENSION_PARAMS:
                    config[key] = value

        # Check if we found any configuration
        if config:
            return {
                "status": "success",
                "extension": extension,
                "config": config
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Extension {extension} not found in pjsip.conf"
            )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error reading PJSIP config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/endpoints/{extension}")
async def get_pjsip_details(extension: str):
    """
    Get PJSIP endpoint details for a specific extension
    """
    try:
        endpoint_details = await ami_client.get_endpoint_details(extension)
        filtered_response = {}
        
        if 'response' in endpoint_details:
            for event in endpoint_details['response']:
                event_type = event.get('Event')
                
                # Skip non-event items and completion events
                if not event_type or event_type in ['EndpointDetailComplete'] or event.get('Response') == 'Success':
                    continue
                    
                if event_type == 'EndpointDetail':
                    filtered_response['endpoint'] = {
                        'type': event.get('ObjectType'),
                        'name': event.get('ObjectName'),
                        'device_state': event.get('DeviceState'),
                        'context': event.get('Context')
                    }
                elif event_type == 'AuthDetail':
                    filtered_response['auth'] = {
                        'username': event.get('Username'),
                        'auth_type': event.get('AuthType')
                    }
                elif event_type == 'AorDetail':
                    filtered_response['aor'] = {
                        'max_contacts': event.get('MaxContacts'),
                        'contacts_registered': event.get('ContactsRegistered', '0')
                    }
                elif event_type == 'ContactStatusDetail' and event.get('URI'):
                    filtered_response['contact'] = {
                        'uri': event.get('URI'),
                        'user_agent': event.get('UserAgent'),
                        'via_address': event.get('ViaAddress'),
                        'status': event.get('Status')
                    }
        
        return {
            "status": "success",
            "extension": extension,
            "details": filtered_response
        }
    except Exception as e:
        logger.error(f"Error getting PJSIP details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_pjsip_config(extension: str = None) -> Dict:
    """
    Get PJSIP configuration for a specific extension
    """
    try:
        config = read_pjsip_conf()
        if extension:
            if extension in config:
                return {
                    "config_exists": True,
                    "type": "endpoint",
                    "max_contacts": config[extension].get("max_contacts", "1"),
                    "callerid": config[extension].get("callerid", f"{extension} <{extension}>")
                }
            return {
                "config_exists": False
            }
        return {
            "config_exists": True,
            "endpoints": config
        }
    except Exception as e:
        logger.error(f"Error reading PJSIP config: {str(e)}")
        return {
            "config_exists": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
