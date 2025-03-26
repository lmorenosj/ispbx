#!/bin/bash
# Example AMI Commands (uncomment the one you want to use):
# =================================================
# 1. Show all PJSIP endpoints:
#Action: PJSIPShowEndpoints

# 2. Show specific endpoint details:
#Action: PJSIPShowEndpoint
#Endpoint: 100

# 3. Show active channels:
#Action: CoreShowChannels

# 4. Show active bridges (calls):
#Action: BridgeList

# 5. Show system status:
#Action: Status

# 6. Show registrations:
#Action: PJSIPShowRegistrationInboundContactStatuses

# 7. Show specific contact status:
#Action: PJSIPShowRegistrationInboundContactStatuses
#ContactUri: 100

# 8. Show endpoint auth:
#Action: PJSIPShowEndpoint
#Endpoint: 100
#ObjectType: auth

# 9. Show endpoint AOR:
#Action: PJSIPShowAors
#Endpoint: 100



# AMI connection details

AMI_HOST="127.0.0.1"
AMI_PORT="5038"
AMI_USER="admin"
AMI_PASS="admin"

# Create a temporary file for the AMI commands
TMP_FILE=$(mktemp)

# Write AMI login and command sequence to temp file
cat << EOF > $TMP_FILE
Action: Login
Username: $AMI_USER
Secret: $AMI_PASS

# Check logs using CLI command
Action: Command
Command: cli show history

# Check all PJSIP endpoints
Action: PJSIPShowEndpoints

# Check specific endpoint details
Action: PJSIPShowEndpoint
Endpoint: 3000

# Check if endpoint is registered
Action: PJSIPShowContacts
Endpoint: 3000

# Check device states
Action: DeviceStateList

Action: Logoff

EOF

# Send commands to AMI using netcat
# The sleep is needed to give AMI time to respond before closing
(cat $TMP_FILE; sleep 2) | nc $AMI_HOST $AMI_PORT

# Clean up
rm $TMP_FILE
