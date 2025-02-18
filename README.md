# ISPBX Manager

A Python-based application to manage and monitor Asterisk PJSIP configuration.

## Project Structure
```
ispbx/
├── backend/
│   ├── src/
│   │   ├── main.py
│   │   └── config/
│   │       ├── pjsip_config.ini
│   │       └── pjsip_detail.ini
│   ├── tests/
│   └── requirements.txt
└── frontend/
```

## Backend Setup

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
cd backend
python src/main.py
```

The API will be available at http://localhost:8000

## Configuration Files

### pjsip_detail.ini
This file defines which parameters should be included in the API response for each type of PJSIP object:

1. **EndpointDetail**: Parameters for endpoint details
   - ObjectType: Endpoint type
   - ObjectName: Extension number
   - DeviceState: Current device state
   - Context: Dialplan context
   - Callerid: Caller ID information

2. **AuthDetail**: Parameters for authentication details
   - ObjectName: Auth name
   - Username: Auth username
   - AuthType: Authentication type
   - Password: Auth password

3. **AorDetail**: Parameters for AOR (Address of Record) details
   - ObjectName: AOR name
   - MaxContacts: Maximum contacts
   - ContactsRegistered: Registered contacts
   - TotalContacts: Total contacts
   - EndpointName: Associated endpoint

## API Documentation

### Base URL
The API is available at `http://localhost:8000`

### Endpoints

#### 1. Get All Endpoints
- **URL:** `/endpoints`
- **Method:** `GET`
- **Description:** Get a list of all PJSIP endpoints
- **Example Response:**
```json
{
  "status": "success",
  "endpoints": [
    {
      "extension": "101",
      "exists_in_config": true,
      "details": {
        "objecttype": "endpoint",
        "objectname": "101",
        "devicestate": "Unavailable",
        "transport": "",
        "aor": "101",
        "auths": "101"
      }
    }
  ]
}
```

#### 2. Get Endpoint Details
- **URL:** `/endpoints/{extension}`
- **Method:** `GET`
- **Description:** Get detailed information about a specific endpoint
- **Example Response:**
```json
{
  "status": "success",
  "extension": "101",
  "details": {
    "endpoint": {
      "objecttype": "endpoint",
      "objectname": "101",
      "devicestate": "Unavailable",
      "context": "internal",
      "callerid": "\"user101\" <101>"
    },
    "auth": {
      "objectname": "101",
      "username": "101",
      "authtype": "userpass",
      "password": "101pass"
    },
    "aor": {
      "objectname": "101",
      "maxcontacts": "1",
      "contactsregistered": "0",
      "totalcontacts": "0",
      "endpointname": "101"
    }
  }
}
```

## Recent Changes (2025-02-08)

### 1. Configuration File Updates
- Updated `pjsip_detail.ini` to use AMI field names (e.g., `ObjectType`, `ObjectName`) for better consistency
- Removed field name mapping from code since we now use AMI field names directly
- All field names in responses are converted to lowercase for consistency

### 2. Code Improvements
- Fixed path issues in `main.py` to use relative paths for config files
- Added detailed logging for debugging AMI responses
- Improved error handling and parameter filtering

### 3. API Response Format
- Standardized response format for both single endpoint and endpoint list endpoints
- Added proper filtering of endpoint details based on `pjsip_detail.ini` configuration
- Improved response structure with clearer organization of endpoint, auth, and AOR details
{
    "message": "ISPBX Manager API"
}
```

#### 2. List All Endpoints
- **URL:** `/endpoints`
- **Method:** `GET`
- **Description:** Get details of all PJSIP endpoints
- **Example Response:**
```json
{
    "status": "success",
    "endpoints": [
        {
            "objectname": "1001",
            "status": "online",
            "type": "endpoint",
            "devicestate": "Unavailable",
            "activechannels": 0
        },
        {
            "objectname": "1002",
            "status": "offline",
            "type": "endpoint",
            "devicestate": "Unavailable",
            "activechannels": 0
        }
    ]
}
```

#### 3. Get Specific Endpoint Details
- **URL:** `/endpoints/{extension}`
- **Method:** `GET`
- **Parameters:** 
  - `extension` (path parameter): The extension number to query
- **Example Request:** `/endpoints/1001`
- **Example Response:**
```json
{
    "status": "success",
    "extension": "1001",
    "details": {
        "objectname": "1001",
        "status": "online",
        "type": "endpoint",
        "devicestate": "Available",
        "activechannels": 0,
        "auths": "1001",
        "aors": "1001"
    }
}
```

#### 4. Get Extension Configuration
- **URL:** `/endpoints/{extension}/config`
- **Method:** `GET`
- **Parameters:**
  - `extension` (path parameter): The extension number to query
- **Example Request:** `/endpoints/1001/config`
- **Example Response:**
```json
{
    "status": "success",
    "extension": "1001",
    "config": {
        "type": "endpoint",
        "transport": "transport-udp",
        "context": "from-internal",
        "disallow": "all",
        "allow": "ulaw",
        "auth": "1001",
        "aors": "1001",
        "direct_media": "no",
        "force_rport": "yes",
        "ice_support": "yes",
        "rewrite_contact": "yes"
    }
}
```

### Error Responses

The API may return the following error responses:

#### 404 Not Found
```json
{
    "detail": "Extension not found"
}
```

#### 500 Internal Server Error
```json
{
    "detail": "Error reading PJSIP configuration"
}
```

### Notes for Frontend Developers

1. **Error Handling**
   - Always check the response status code
   - Handle network errors gracefully
   - Display error messages from the `detail` field to users

2. **Polling Considerations**
   - When displaying endpoint status, consider polling the `/endpoints` endpoint every 5-10 seconds
   - Implement exponential backoff if the server becomes unresponsive

3. **Data Formatting**
   - Status can be either "online" or "offline"
   - Extension numbers are strings, not numbers
   - Configuration values are all strings

4. **Security**
   - The API currently doesn't require authentication
   - All requests should be made over HTTPS in production
   - Consider implementing rate limiting in your frontend

## Note
- The application needs access to `/etc/asterisk/pjsip.conf`
- Make sure you have appropriate permissions to read the configuration file
- For production use, consider implementing proper authentication and security measures
