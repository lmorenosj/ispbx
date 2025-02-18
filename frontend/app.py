from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
from datetime import datetime
import threading
import time
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
socketio = SocketIO(app, async_mode='threading', ping_timeout=10)

API_BASE_URL = 'http://localhost:8000'

# Configure requests session with retries and connection pooling
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504]
)
http_adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=10,
    pool_maxsize=10
)
session.mount('http://', http_adapter)
session.mount('https://', http_adapter)

def handle_backend_events():
    """Handle real-time events from the backend Socket.IO"""
    import socketio
    
    # Create Socket.IO client
    sio = socketio.Client(logger=True, engineio_logger=True)
    
    @sio.event
    def connect():
        logger.info('Connected to backend Socket.IO')
    
    @sio.event
    def disconnect():
        logger.info('Disconnected from backend Socket.IO')
    
    @sio.on('endpoint_status')
    def on_endpoint_status(data):
        logger.info(f'Received endpoint status: {data}')
        socketio.emit('endpoint_status_update', data)
    
    @sio.on('active_calls')
    def on_active_calls(data):
        logger.info(f'Received active calls: {data}')
        socketio.emit('active_calls_update', data)
    
    while True:
        try:
            logger.info('Connecting to backend Socket.IO...')
            sio.connect('http://localhost:8000', transports=['websocket'])
            sio.wait()
        except Exception as e:
            logger.error(f'Socket.IO connection error: {e}')
            time.sleep(5)  # Wait before retrying

if __name__ == '__main__':
    try:
        # Start the background thread for WebSocket connection
        websocket_thread = threading.Thread(target=handle_backend_events)
        websocket_thread.daemon = True
        websocket_thread.start()
        logger.info("Started WebSocket client thread")
        
        # Run the Flask-SocketIO app
        logger.info("Starting Flask-SocketIO server...")
        socketio.run(app, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        exit(1)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/endpoints/<extension>')
def get_endpoint_details(extension):
    try:
        response = session.get(
            f"{API_BASE_URL}/endpoints/{extension}",
            timeout=5
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/extensions')
def extensions():
    return render_template('extensions/list.html')

@app.route('/calls')
def active_calls():
    return render_template('active_calls.html')

def fetch_active_calls():
    """Fetch active calls and emit to connected clients"""
    last_valid_calls = None  # Keep track of last valid calls
    update_interval = 2  # Time between updates in seconds
    
    while True:
        try:
            response = session.get(
                f"{API_BASE_URL}/api/calls/active",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    last_valid_calls = data
                    socketio.emit('active_calls_update', data)
            elif last_valid_calls is not None:
                # If current fetch failed but we have previous data, use it
                print("Using last valid calls data")
                socketio.emit('active_calls_update', last_valid_calls)
        except Exception as e:
            print(f"Error fetching active calls: {e}")
            if last_valid_calls is not None:
                socketio.emit('active_calls_update', last_valid_calls)
        
        time.sleep(update_interval)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # Initial data fetch
    try:
        # Fetch endpoints
        response = session.get(f"{API_BASE_URL}/endpoints")
        if response.status_code == 200:
            emit('endpoints_update', response.json())
            
        # Fetch active calls
        response = session.get(f"{API_BASE_URL}/api/calls/active")
        if response.status_code == 200:
            emit('active_calls_update', response.json())
    except Exception as e:
        print(f"Error on initial data fetch: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    try:
        # Start the background thread for WebSocket connection
        websocket_thread = threading.Thread(target=handle_backend_events)
        websocket_thread.daemon = True
        websocket_thread.start()
        logger.info("Started WebSocket client thread")
        
        # Run the Flask-SocketIO app
        logger.info("Starting Flask-SocketIO server...")
        socketio.run(app, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        exit(1)
