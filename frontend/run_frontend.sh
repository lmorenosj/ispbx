#!/bin/bash



# Set the backend directory path
FRONTEND_DIR="/home/ubuntu/Documents/ispbx/frontend"
VENV_DIR="/home/ubuntu/Documents/ispbx/frontend/venv"


# Change to backend directory
cd $FRONTEND_DIR
 

# Activate virtual environment
source $VENV_DIR/bin/activate

# Install requirements if requirements.txt exists
if [ -f "$FRONTEND_DIR/requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r $FRONTEND_DIR/requirements.txt
fi



# Run the backend application
# Assuming the main file is app.py, modify this if it's different
echo "Starting backend server..."
# Run the test script with verbose output
python -m pytest app.py -v || python app.py
