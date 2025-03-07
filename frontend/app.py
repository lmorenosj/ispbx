from flask import Flask, render_template, request, Response
import socketio
from flask_socketio import SocketIO
from flask_cors import CORS
import logging
import threading
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Initialize Socket.IO with Flask
socketio_app = SocketIO(app, cors_allowed_origins="*")

# Backend connection configuration
SOCKETIO_SERVER = 'http://127.0.0.1:8000'

# Client for connecting to backend
sio_client = socketio.Client(
    logger=False,
    reconnection=True,
    reconnection_attempts=5,
    reconnection_delay=1,
    reconnection_delay_max=5
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/endpoints', methods=['GET'])
def proxy_endpoints():
    # Forward the request to the backend API
    resp = requests.get('http://127.0.0.1:8000/api/endpoints')
    # Return the response with the same status code, headers, and content
    return Response(
        resp.content,
        status=resp.status_code,
        content_type=resp.headers.get('content-type')
    )
@sio_client.event
def connect():
    print("Connected to Socket.IO server!")
    logger.info("Connected to Socket.IO server")

@sio_client.event
def connect_error(data):
    logger.error(f"Socket.IO connection error: {data}")

@sio_client.event
def disconnect():
    logger.warning("Disconnected from Socket.IO server")

# Connect to backend in a separate thread
def connect_to_backend():
    try:
        logger.info(f"Attempting connection to backend at {SOCKETIO_SERVER}")
        sio_client.connect(SOCKETIO_SERVER)
    except socketio.exceptions.ConnectionError as e:
        logger.error(f"Failed to connect to Socket.IO backend: {e}")
    except Exception as e:
        logger.error(f"Unexpected error connecting to backend: {e}")

if __name__ == '__main__':
    # Start backend connection in a thread
    threading.Thread(target=connect_to_backend, daemon=True).start()
    
    # Start Flask-SocketIO app
    socketio_app.run(app, host='0.0.0.0', port=5000, debug=True)