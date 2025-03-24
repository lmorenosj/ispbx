# ISPBX - Manual API Testing Guide

This document provides instructions for manually testing all features in the ISPBX backend API via command line interface (CLI).

## Prerequisites

- [curl](https://curl.se/) - Command line tool for making HTTP requests
- [jq](https://stedolan.github.io/jq/) - Command line JSON processor (optional but recommended for better output formatting)

## API Endpoints

The backend server runs on `http://localhost:8000` by default. All examples below assume this base URL.

### 1. Health Check

Check if the API is running:

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "message": "ISPBX Manager API",
  "status": "healthy",
  "version": "1.0.0"
}
```

### 2. Endpoint Management

#### 2.1 List All Endpoints (AMI)

Get all endpoints from Asterisk via AMI:

```bash
curl http://localhost:8000/api/endpoints | jq
```

#### 2.2 Get Specific Endpoint Details (AMI)

Get details for a specific endpoint via AMI:

```bash
curl http://localhost:8000/api/endpoints/1001 | jq
```

#### 2.3 List All Endpoints (Database)

Get all endpoints from the database:

```bash
curl http://localhost:8000/api/endpoints/db | jq
```

#### 2.4 Get Specific Endpoint Details (Database)

Get details for a specific endpoint from the database:

```bash
curl http://localhost:8000/api/endpoints/db/1001 | jq
```

#### 2.5 Create New Endpoint

Create a new SIP endpoint:

```bash
curl -X POST http://localhost:8000/api/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "1010",
    "password": "securepassword",
    "name": "Test User",
    "context": "from-internal",
    "codecs": ["g722", "ulaw", "alaw"]
  }' | jq
```

#### 2.6 Update Existing Endpoint

Update an existing endpoint:

```bash
curl -X PUT http://localhost:8000/api/endpoints/1010 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated User",
    "context": "from-internal",
    "codecs": ["g722", "ulaw"]
  }' | jq
```

Update just the password:

```bash
curl -X PUT http://localhost:8000/api/endpoints/1010 \
  -H "Content-Type: application/json" \
  -d '{
    "password": "newpassword"
  }' | jq
```

#### 2.7 Delete Endpoint

Delete an existing endpoint:

```bash
curl -X DELETE http://localhost:8000/api/endpoints/1010 | jq
```

## Testing Scenarios

### Complete CRUD Test Sequence

The following sequence tests the entire CRUD (Create, Read, Update, Delete) cycle for endpoints:

```bash
# 1. Create a new endpoint
curl -X POST http://localhost:8000/api/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "2001",
    "password": "test123",
    "name": "Test Extension",
    "context": "from-internal",
    "codecs": ["g722", "ulaw"]
  }' | jq

# 2. Verify it exists in the database
curl http://localhost:8000/api/endpoints/db/2001 | jq

# 3. Verify it exists in Asterisk
curl http://localhost:8000/api/endpoints/2001 | jq

# 4. Update the endpoint
curl -X PUT http://localhost:8000/api/endpoints/2001 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Extension",
    "codecs": ["g722", "ulaw", "alaw"]
  }' | jq

# 5. Verify the update in the database
curl http://localhost:8000/api/endpoints/db/2001 | jq

# 6. Delete the endpoint
curl -X DELETE http://localhost:8000/api/endpoints/2001 | jq

# 7. Verify it's deleted
curl http://localhost:8000/api/endpoints/db/2001
# Should return a 404 error
```

### Testing Error Handling

#### Create Duplicate Endpoint

```bash
# First create an endpoint
curl -X POST http://localhost:8000/api/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "3001",
    "password": "test123",
    "name": "Test Extension",
    "context": "from-internal"
  }' | jq

# Try to create the same endpoint again
curl -X POST http://localhost:8000/api/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "3001",
    "password": "test123",
    "name": "Test Extension",
    "context": "from-internal"
  }' | jq
# Should return a 409 conflict error
```

#### Update Non-existent Endpoint

```bash
curl -X PUT http://localhost:8000/api/endpoints/9999 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Non-existent Extension"
  }' | jq
# Should return a 404 not found error
```

#### Delete Non-existent Endpoint

```bash
curl -X DELETE http://localhost:8000/api/endpoints/9999 | jq
# Should return a 404 not found error
```

## Tips for Testing

1. Use `jq` to format JSON responses for better readability:
   ```bash
   curl http://localhost:8000/api/endpoints | jq
   ```

2. Save common test commands in a shell script for easy reuse:
   ```bash
   # test_api.sh
   #!/bin/bash
   
   BASE_URL="http://localhost:8000"
   
   # Test health check
   echo "Testing health check..."
   curl -s $BASE_URL | jq
   
   # More test commands...
   ```

3. Use environment variables for test data:
   ```bash
   ENDPOINT_ID="5001"
   curl -X POST http://localhost:8000/api/endpoints \
     -H "Content-Type: application/json" \
     -d "{
       \"endpoint_id\": \"$ENDPOINT_ID\",
       \"password\": \"test123\",
       \"name\": \"Test Extension $ENDPOINT_ID\"
     }" | jq
   ```

4. Check HTTP status codes:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/endpoints/9999
   # Should return 404
   ```

## Troubleshooting

- If you get connection refused errors, make sure the backend server is running.
- If you get 500 errors, check the server logs for more details.
- If AMI-related endpoints fail, ensure Asterisk is running and the AMI connection is properly configured.
