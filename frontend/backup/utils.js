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

// Socket.IO connection management
function initializeSocketConnection(endpointMonitor, callMonitor) {

    const monitor = endpointMonitor;
    const socket = io();
    const connectionStatus = document.getElementById('connection-status');

    // Frontend socket connection events
    socket.on('connect', () => {
        connectionStatus.textContent = 'Connected';
        connectionStatus.classList.remove('connection-disconnected');
        connectionStatus.classList.add('connection-connected');
    });

    socket.on('disconnect', () => {
        console.log('[Frontend] Socket disconnected from frontend server');
        connectionStatus.textContent = 'Frontend Disconnected';
        connectionStatus.classList.remove('connection-connected');
        connectionStatus.classList.add('connection-disconnected');
    });

    socket.on('connect_error', (error) => {
        console.error('[Frontend] Socket connection error:', error);
        connectionStatus.textContent = 'Connection Error';
        connectionStatus.classList.remove('connection-connected');
        connectionStatus.classList.add('connection-disconnected');
    });

    // Backend connection status events
    socket.on('backendConnected', (data) => {
        console.log('[Backend] Connected to AMI server');
        connectionStatus.textContent = 'Backend Connected';
    });

    socket.on('backendDisconnected', (data) => {
        console.warn('[Backend] Disconnected from AMI server');
        connectionStatus.textContent = 'Backend Disconnected';
    });

    socket.on('backendError', (data) => {
        console.error('[Backend] Connection error:', data.error);
        connectionStatus.textContent = 'Backend Error';
    });

    // Listen for EndpointState events
    socket.on('EndpointState', (event) => {
        const eventData = event.Event ? event : (event.data || event);
        
        if (!eventData?.Device || !eventData?.State) {
            return;
        }
    
        if (monitor?.handleEvent) {
            console.log(`[Event] Endpoint ${eventData.Device} state: ${eventData.State}`);
            monitor.handleEvent(eventData);
        }
    });

    // Listen for EndpointCallState events
    socket.on('EndpointCallState', (event) => {
        const eventData = event.Event ? event : (event.data || event);
        
        if (!eventData?.Event) {
            return;
        }
    
        if (callMonitor?.handleEvent) {
            console.log(`[Event] Call ${eventData.Event}`);
            callMonitor.handleEvent(eventData);
        }
    });

    return socket;
}
