// Format timestamp
function formatTimestamp(timestamp) {
    return new Date().toLocaleTimeString();
}

// Format duration in seconds to mm:ss format
function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// API endpoints configuration
const API_CONFIG = {
    // Backend server URL
    BACKEND_URL: 'http://localhost:8000',
    
    // API endpoints
    ENDPOINTS: {
        LIST: '/api/endpoints',
        DB_LIST: '/api/endpoints/db',
        GET: (id) => `/api/endpoints/${id}`,
        DB_GET: (id) => `/api/endpoints/db/${id}`,
        CREATE: '/api/endpoints',
        UPDATE: (id) => `/api/endpoints/${id}`,
        DELETE: (id) => `/api/endpoints/${id}`
    },
    QUEUES: {
        LIST: '/api/queues',
        DB_LIST: '/api/queues/db',
        GET: (id) => `/api/queues/${id}`,
        DB_GET: (id) => `/api/queues/db/${id}`,
        CREATE: '/api/queues',
        UPDATE: (id) => `/api/queues/${id}`,
        DELETE: (id) => `/api/queues/${id}`
    },
    QUEUE_MEMBERS: {
        ADD: (queueName) => `/api/queues/${queueName}/members`,
        UPDATE: (queueName, interfaceName) => `/api/queues/${queueName}/members/${interfaceName}`,
        REMOVE: (queueName, interfaceName) => `/api/queues/${queueName}/members/${interfaceName}`,
        LIST: (queueName) => `/api/queues/${queueName}/members`
    }
};

// Socket.IO connection management
function initializeSocketConnection(endpointMonitor, callMonitor) {
    const monitor = endpointMonitor;
    const connectionStatus = document.getElementById('connection-status');

    // Connect directly to the backend Socket.IO server
    console.log(`Connecting directly to backend Socket.IO server at ${API_CONFIG.BACKEND_URL}`);
    const socket = io(API_CONFIG.BACKEND_URL, {
        reconnectionAttempts: 10,
        reconnectionDelay: 2000,
        timeout: 10000,
        withCredentials: false,
        transports: ['websocket', 'polling']
    });

    // Socket connection events
    socket.on('connect', () => {
        console.log('[Socket.IO] Connected directly to backend server');
        connectionStatus.textContent = 'Connected';
        connectionStatus.classList.remove('connection-disconnected');
        connectionStatus.classList.add('connection-connected');
    });

    socket.on('disconnect', () => {
        console.log('[Socket.IO] Disconnected from backend server');
        connectionStatus.textContent = 'Disconnected';
        connectionStatus.classList.remove('connection-connected');
        connectionStatus.classList.add('connection-disconnected');
    });

    socket.on('connect_error', (error) => {
        console.error('[Socket.IO] Connection error:', error);
        connectionStatus.textContent = 'Connection Error';
        connectionStatus.classList.remove('connection-connected');
        connectionStatus.classList.add('connection-disconnected');
    });

    // Listen for DeviceStateChange events and transform to EndpointState
    // This maintains consistent endpoint terminology
    socket.on('DeviceStateChange', (event) => {
        console.log('[Event] DeviceStateChange received:', event);
        
        // Extract the actual data from the nested structure
        const data = event.data || event;
        
        if (!data.Device && !data.State) {
            console.warn('Invalid DeviceStateChange event data:', event);
            return;
        }
        
        // Transform to preferred endpoint terminology
        const endpointData = {
            EndpointId: data.Device || data.Endpoint || data.endpoint_id,
            State: data.State || data.status,
            StateText: data.StateText || '',
            // Include any additional fields from the original data
            ...data
        };
        
        if (monitor?.handleEvent) {
            monitor.handleEvent(endpointData);
        }
    });
    
    // Also listen for individual call events for backward compatibility
    function processEvent(event) {
        // Extract the actual data from the nested structure
        const data = event.data || event;
        
        if (!data.Event) {
            // If the event doesn't have an Event property, set it to the event name
            data.Event = event.name || 'Unknown';
        }
        
        if (callMonitor?.handleEvent) {
            console.log(`[Event] Individual call event (${data.Event}`);
            callMonitor.handleEvent(data);
        }
    }

    // Listen for call-related events
    socket.on('Newchannel', processEvent);
    socket.on('DialState', processEvent);
    socket.on('DialEnd', processEvent);
    socket.on('Hangup', processEvent);

    return socket;
}

// API helper functions
async function fetchAPI(segment, options = {}) {
    const url = `${API_CONFIG.BACKEND_URL}${segment}`;
    
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        const data = await response.json();
        return { status: response.status, data };
    } catch (error) {
        console.error(`API Error (${url}):`, error);
        throw error;
    }
}
