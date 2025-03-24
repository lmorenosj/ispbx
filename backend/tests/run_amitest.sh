#!/bin/bash

# Set the backend directory path
BACKEND_DIR="/home/ubuntu/Documents/ispbx/backend"
VENV_DIR="/home/ubuntu/Documents/ispbx/backend/venv"


# Change to backend directory
cd $BACKEND_DIR

# Clear api logs
echo "Clearing logs"
truncate -s 0 logs/api.log
truncate -s 0 logs/errors.log
truncate -s 0 logs/ami_events.log
truncate -s 0 logs/ami_responses.log
truncate -s 0 logs/ami.log
truncate -s 0 logs/uvicorn.log
truncate -s 0 logs/uvicorn_access.log

 

# Activate virtual environment
source $VENV_DIR/bin/activate


echo "Running tests for all extensions"
PYTHONPATH=$BACKEND_DIR/src python3 tests/endpoint_monitor_test.py