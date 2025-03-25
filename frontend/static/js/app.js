// Global instances
let endpointMonitor;
let endpointManager;
let callMonitor;
let socket;

// Application initialization
document.addEventListener('DOMContentLoaded', async () => {
    console.info('DOM content loaded, initializing application...');
    
    // Display connection status
    const connectionStatus = document.getElementById('connection-status');
    connectionStatus.textContent = 'Connecting...';
    connectionStatus.classList.add('connection-connecting');
    
    try {
        // Initialize socket connection first to ensure we have connectivity
        console.info(`Initializing direct Socket.IO connection to backend at ${API_CONFIG.BACKEND_URL}`);
        
        // Initialize endpoint monitor
        console.debug('Creating EndpointMonitor instance');
        endpointMonitor = new EndpointMonitor();
        console.debug('EndpointMonitor created');
        
        // Initialize call monitor
        console.debug('Creating CallMonitor instance');
        callMonitor = new CallMonitor();
        console.debug('CallMonitor created');
        
        // Connect to Socket.IO server
        socket = initializeSocketConnection(endpointMonitor, callMonitor);
        console.info('Socket connection initialized');
        
        // Make socket available globally for debugging
        window.socket = socket;
        
        // Initialize endpoint manager with socket
        console.debug('Creating EndpointManager instance');
        endpointManager = new EndpointManager();
        console.debug('EndpointManager created');
        endpointManager.initialize();
        console.debug('EndpointManager initialized');
        
        // Initialize monitors after socket connection is established
        endpointMonitor.initialize();
        console.debug('EndpointMonitor initialized');
        callMonitor.initialize();
        console.debug('CallMonitor initialized');
        
        // Make instances available globally for debugging
        window.endpointMonitor = endpointMonitor;
        window.endpointManager = endpointManager;
        window.callMonitor = callMonitor;
        
        console.info('Application initialization completed successfully');
    } catch (error) {
        console.error('Error during application initialization:', error);
        connectionStatus.textContent = 'Connection Error';
        connectionStatus.classList.remove('connection-connecting');
        connectionStatus.classList.add('connection-disconnected');
        
        // Display error message to user
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger mt-3';
        errorAlert.textContent = `Failed to initialize application: ${error.message}`;
        document.querySelector('.container').prepend(errorAlert);
    }
});