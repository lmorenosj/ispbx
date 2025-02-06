from fastapi import FastAPI, HTTPException
import os
from typing import Dict, Optional
import logging
from datetime import datetime
from ami_client import AmiClient

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

def parse_endpoint_config(raw_config: Dict) -> Dict:
    """
    Parse and organize endpoint configurations into a simplified format
    """
    endpoints = {}
    
    # First pass: collect all sections by type
    endpoint_sections = {}
    
    for section, params in raw_config.items():
        # Skip transport and general sections
        if section == "general" or section.startswith("transport-"):
            continue
            
        # Get the endpoint number
        section_number = None
        if section.isdigit():
            section_number = section
            
        if section_number:
            if section_number not in endpoint_sections:
                endpoint_sections[section_number] = {"endpoint": {}, "auth": {}, "aor": {}}
            
            # Determine the type based on the parameters
            section_type = params.get("type", "")
            # Special handling for auth sections
            if section_type == "auth" or "auth_type" in params:
                section_type = "auth"
                
            if section_type in ["endpoint", "auth", "aor"]:
                endpoint_sections[section_number][section_type].update(params)

    # Second pass: organize into final format
    for number, sections in endpoint_sections.items():
        endpoint_data = sections["endpoint"]
        auth_data = sections["auth"]
        aor_data = sections["aor"]
        
        # Get callerid from endpoint section
        callerid = endpoint_data.get("callerid", f"user{number} <{number}>")
        
        endpoints[number] = {
            "type": "endpoint",
            "max_contacts": aor_data.get("max_contacts", "1"),
            "username": auth_data.get("username", number),
            "password": auth_data.get("password", ""),
            "callerid": callerid.strip()
        }
    
    return endpoints

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
                    
        return parse_endpoint_config(config)
    except Exception as e:
        logger.error(f"Error reading PJSIP configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Error reading PJSIP configuration")

@app.get("/")
async def root():
    return {"message": "ISPBX Manager API"}

@app.get("/pjsip")
@app.get("/pjsip/{extension}")
async def get_pjsip_details(extension: str = None):
    """
    Get PJSIP endpoint details, optionally filtered by extension
    """
    try:
        endpoint_details = await ami_client.get_endpoint_details(extension)
        
        if extension is None:
            return {
                "status": "success",
                "endpoints": endpoint_details.get('endpoints', [])
            }
        else:
            return {
                "status": "success",
                "extension": extension,
                "details": endpoint_details
            }
    except Exception as e:
        logger.error(f"Error getting PJSIP details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pjsip/{extension}/config")
async def get_pjsip_extension_config(extension: str):
    """
    Get PJSIP configuration for a specific extension from pjsip.conf
    """
    try:
        config = read_pjsip_conf()
        if extension in config:
            return {
                "status": "success",
                "extension": extension,
                "config": config[extension]
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

@app.get("/pjsip/status")
@app.get("/pjsip/status/{extension}")
async def get_pjsip_status(extension: str = None):
    """
    Get the current PJSIP status, optionally filtered by extension
    """
    try:
        # Get detailed endpoint information
        endpoint_details = await ami_client.get_endpoint_details(extension)
        
        if extension is None:
            # Process all endpoints
            all_endpoints = []
            for endpoint in endpoint_details.get('endpoints', []):
                ext = endpoint['extension']
                details = process_endpoint_details(endpoint)
                all_endpoints.append({
                    "extension": ext,
                    "details": details
                })
            return {
                "status": "success",
                "endpoints": all_endpoints
            }
        else:
            # Process single endpoint
            details = process_endpoint_details(endpoint_details)
            return {
                "status": "success",
                "extension": extension,
                "details": details
            }
    except Exception as e:
        logger.error(f"Error getting PJSIP status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

def process_endpoint_details(endpoint_details: Dict) -> Dict:
    """
    Process endpoint details from AMI response
    """
    endpoint_info = {}
    auth_info = {}
    aor_info = {}
    contact_info = {}
    registration_status = "UNREGISTERED"
    
    if 'response' in endpoint_details:
        for event in endpoint_details['response']:
            if event.get('Event') == 'EndpointDetail':
                endpoint_info = {
                    'device_state': event.get('DeviceState'),
                    'callerid': event.get('Callerid'),
                    'context': event.get('Context'),
                    'codecs': event.get('Allow'),
                    'dtmf_mode': event.get('DtmfMode')
                }
            elif event.get('Event') == 'AuthDetail':
                auth_info = {
                    'username': event.get('Username'),
                    'auth_type': event.get('AuthType')
                }
            elif event.get('Event') == 'AorDetail':
                aor_info = {
                    'contacts': event.get('Contacts'),
                    'contacts_registered': event.get('ContactsRegistered'),
                    'max_contacts': event.get('MaxContacts')
                }
                if int(event.get('ContactsRegistered', 0)) > 0:
                    registration_status = "REGISTERED"
            elif event.get('Event') == 'ContactStatusDetail':
                contact_info = {
                    'status': event.get('Status'),
                    'uri': event.get('URI'),
                    'user_agent': event.get('UserAgent'),
                    'reg_expire': event.get('RegExpire'),
                    'via_address': event.get('ViaAddress')
                }
    
    return {
        "exists_in_config": endpoint_details.get('exists_in_config', False),
        "registration_status": registration_status,
        "endpoint": endpoint_info,
        "auth": auth_info,
        "aor": aor_info,
        "contact": contact_info
    }

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
