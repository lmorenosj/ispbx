from flask import Flask, render_template, request, Response
import socketio
from flask_socketio import SocketIO
from flask_cors import CORS
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure AMI event logging
ami_logger = logging.getLogger('ami_events')
ami_logger.setLevel(logging.INFO)

# Create file handler for AMI events
ami_handler = logging.FileHandler('ami_events.log')
ami_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
ami_logger.addHandler(ami_handler)

# Create Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Initialize Flask-SocketIO with threading mode
socketio_app = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Backend connection configuration
SOCKETIO_SERVER = 'http://127.0.0.1:8000'

# Client for connecting to backend
sio_client = socketio.Client(logger=True, reconnection=True)

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint API proxy routes
@app.route('/api/endpoints', methods=['GET'])
def get_endpoints():
    resp = requests.get('http://127.0.0.1:8000/api/endpoints')
    logger.info(f"GET /api/endpoints: {resp.status_code}")
    return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('content-type'))

@app.route('/api/endpoints/<endpoint_id>', methods=['GET'])
def get_endpoint(endpoint_id):
    resp = requests.get(f'http://127.0.0.1:8000/api/endpoints/{endpoint_id}')
    logger.info(f"GET /api/endpoints/{endpoint_id}: {resp.status_code}")
    return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('content-type'))

@app.route('/api/endpoints/db', methods=['GET'])
def get_db_endpoints():
    resp = requests.get('http://127.0.0.1:8000/api/endpoints/db')
    logger.info(f"GET /api/endpoints/db: {resp.status_code}")
    return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('content-type'))

@app.route('/api/endpoints/db/<endpoint_id>', methods=['GET'])
def get_db_endpoint(endpoint_id):
    resp = requests.get(f'http://127.0.0.1:8000/api/endpoints/db/{endpoint_id}')
    logger.info(f"GET /api/endpoints/db/{endpoint_id}: {resp.status_code}")
    return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('content-type'))

@app.route('/api/endpoints', methods=['POST'])
def create_endpoint():
    resp = requests.post(
        'http://127.0.0.1:8000/api/endpoints',
        json=request.json,
        headers={'Content-Type': 'application/json'}
    )
    return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('content-type'))

@app.route('/api/endpoints/<endpoint_id>', methods=['PUT'])
def update_endpoint(endpoint_id):
    resp = requests.put(
        f'http://127.0.0.1:8000/api/endpoints/{endpoint_id}',
        json=request.json,
        headers={'Content-Type': 'application/json'}
    )
    return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('content-type'))

@app.route('/api/endpoints/<endpoint_id>', methods=['DELETE'])
def delete_endpoint(endpoint_id):
    resp = requests.delete(f'http://127.0.0.1:8000/api/endpoints/{endpoint_id}')
    return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('content-type'))

@sio_client.event
def connect():
    logger.info("Connected to Socket.IO server")
    socketio_app.emit('backendConnected', {'status': 'connected'})

@sio_client.on('DeviceStateChange')
def endpointState_handler(data):
    socketio_app.emit('EndpointState', data)
    logger.info(f"Emitting EndpointState event to front: {data}")
    ami_logger.info(f"DeviceStateChange: {data}")

@sio_client.on('Newchannel')
@sio_client.on('DialState')
@sio_client.on('DialEnd')
@sio_client.on('Hangup')
def endpointCallState_handler(data):
    logger.info(f"Emitting EndpointCallState event to front: {data}")
    socketio_app.emit('EndpointCallState', data)
    ami_logger.info(f"{data.get('Event', 'Unknown')}: {data}")

@sio_client.event
def connect_error(data):
    logger.error(f"Socket.IO connection error: {data}")
    socketio_app.emit('backendError', {'error': str(data)})

@sio_client.event
def disconnect():
    logger.warning("Disconnected from Socket.IO server")
    socketio_app.emit('backendDisconnected', {'status': 'disconnected'})

# Connect to backend in a background task
def connect_to_backend():
    try:
        logger.info(f"Attempting connection to backend at {SOCKETIO_SERVER}")
        sio_client.connect(SOCKETIO_SERVER)
        sio_client.wait()  # Keep the connection alive
    except socketio.exceptions.ConnectionError as e:
        logger.error(f"Failed to connect to Socket.IO backend: {e}")
        socketio_app.emit('backendError', {'error': str(e)})
    except Exception as e:
        logger.error(f"Unexpected error connecting to backend: {e}")
        socketio_app.emit('backendError', {'error': str(e)})

if __name__ == '__main__':
    # Start backend connection in a Flask-SocketIO managed thread
    socketio_app.start_background_task(connect_to_backend)

    # Start Flask-SocketIO app
    socketio_app.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
