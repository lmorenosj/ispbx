#!/bin/bash

# Set the backend directory path
BACKEND_DIR="/home/ubuntu/Documents/ispbx/backend"
VENV_DIR="/home/ubuntu/Documents/ispbx/backend/venv"

# Set the backend directory path with 172.16.4.50
#BACKEND_DIR="/home/tier1/ispbx/backend"
#VENV_DIR="/home/tier1/ispbx/backend/venv"



# Change to backend directory
cd $BACKEND_DIR

# Create logs directory if it doesn't exist
mkdir -p logs

# Clear api logs if they exist
echo "Clearing logs"
touch logs/api.log logs/errors.log logs/ami_events.log logs/ami_responses.log logs/ami.log logs/uvicorn.log logs/uvicorn_access.log
truncate -s 0 logs/api.log
truncate -s 0 logs/errors.log
truncate -s 0 logs/ami_events.log
truncate -s 0 logs/ami_responses.log
truncate -s 0 logs/ami.log
truncate -s 0 logs/uvicorn.log
truncate -s 0 logs/uvicorn_access.log

 

# Activate virtual environment
source $VENV_DIR/bin/activate

# Install requirements if requirements.txt exists
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    echo "Installing dependencies..."
    pip3 install -r $BACKEND_DIR/requirements.txt
fi

# Install aiomysql for endpoint management
pip3 install aiomysql


# Run the backend application
# Assuming the main file is app.py, modify this if it's different
echo "Starting backend server..."
python3 src/main.py
#uvicorn src.main:socket_app --host 0.0.0.0 --port 8000 --reload
