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

# Install requirements if requirements.txt exists
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r $BACKEND_DIR/requirements.txt
fi



# Run the backend application
# Assuming the main file is app.py, modify this if it's different
echo "Starting backend server..."
#python src/main2.py
uvicorn src.main:socket_app --host 0.0.0.0 --port 8000 --reload
