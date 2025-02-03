from fastapi import FastAPI, HTTPException
import os
from typing import Dict, Optional
import logging

app = FastAPI(title="ISPBX Manager", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PJSIP_CONF_PATH = "/etc/asterisk/pjsip.conf"

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
        callerid = endpoint_data.get("callerid", "user%s <%s>" % (number, number))
        
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
                    # Don't overwrite existing sections, create a new dict for the section
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

@app.get("/pjsip/config")
@app.get("/pjsip/config/{extension}")
async def get_pjsip_config(extension: str = None):
    """
    Get all endpoint configurations or a specific extension
    """
    try:
        config = read_pjsip_conf()
        if extension:
            if extension in config:
                return {
                    "status": "success",
                    "extension": extension,
                    "config": config[extension]
                }
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Extension {extension} not found"
                )
        return {"status": "success", "endpoints": config}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pjsip/status")
@app.get("/pjsip/status/{extension}")
async def get_pjsip_status(extension: str = None):
    """
    Get the current PJSIP status, optionally filtered by extension
    """
    try:
        config = read_pjsip_conf()
        
        if extension:
            if extension in config:
                endpoint_config = config[extension]
                return {
                    "status": "success",
                    "extension": extension,
                    "details": {
                        "config_exists": True,
                        "registration_status": "Registered",  # This would need actual Asterisk AMI integration
                        "endpoint_type": endpoint_config["type"],
                        "max_contacts": endpoint_config["max_contacts"],
                        "contact_status": "Available",  # This would need actual Asterisk AMI integration
                        "callerid": endpoint_config["callerid"],
                        "last_registration": "2025-02-03 00:50:48",  # This would need actual Asterisk AMI integration
                        "ip_address": "Unknown"  # This would need actual Asterisk AMI integration
                    }
                }
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Extension {extension} not found"
                )
                
        return {
            "status": "success",
            "details": {
                "total_endpoints": len(config),
                "endpoints": list(config.keys()),
                "config_file": PJSIP_CONF_PATH,
                "config_exists": os.path.exists(PJSIP_CONF_PATH)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
