/**
 * CDR Application Initialization
 * Separate from the main dashboard app.js to avoid dependency issues
 */

// Global instance
let cdrManager;
let socket;

// Application initialization
document.addEventListener('DOMContentLoaded', async () => {
    console.info('DOM content loaded, initializing CDR application...');
    
    // Display connection status
    const connectionStatus = document.getElementById('connection-status');
    connectionStatus.textContent = 'Connecting...';
    connectionStatus.classList.add('connection-connecting');
    
    try {
        // Initialize socket connection first to ensure we have connectivity
        console.info(`Initializing direct Socket.IO connection to backend at ${API_CONFIG.BACKEND_URL}`);
        
        // Connect to Socket.IO server with minimal functionality for CDR page
        socket = io(API_CONFIG.BACKEND_URL, {
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
        
        // Make socket available globally for debugging
        window.socket = socket;
        
        // Initialize CDR manager
        console.debug('Creating CDRManager instance');
        cdrManager = new CDRManager();
        console.debug('CDRManager created');
        
        // Make instance available globally for debugging
        window.cdrManager = cdrManager;
        
        console.info('CDR application initialization completed successfully');
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
