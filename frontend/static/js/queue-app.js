/**
 * ISPBX Queue Dashboard Application
 * 
 * This script initializes the queue dashboard components and establishes
 * the Socket.IO connection to the backend server.
 */

// Socket.IO connection
let socket;

// Connection status indicator
const connectionStatus = document.getElementById('connection-status');

// Refresh button and indicator
const refreshBtn = document.getElementById('refresh-btn');
const refreshIndicator = document.getElementById('refresh-indicator');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.info('Initializing Queue Dashboard Application');
    
    // Initialize Socket.IO connection
    initializeSocketConnection();
    
    // Set up refresh button
    refreshBtn.addEventListener('click', () => {
        refreshData();
    });
    
    // Hide refresh indicator initially
    refreshIndicator.style.display = 'none';
});

// Initialize Socket.IO connection
function initializeSocketConnection() {
    // Get backend URL from the current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = 8000; // Backend port
    const backendUrl = `${protocol}//${host}:${port}`;
    
    console.info(`Connecting to backend at ${backendUrl}`);
    
    // Initialize Socket.IO connection
    socket = io(backendUrl, {
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: Infinity,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000
    });
    
    // Connection event handlers
    socket.on('connect', () => {
        console.info('Connected to backend');
        updateConnectionStatus(true);
        
        // Initial data refresh
        refreshData();
    });
    
    socket.on('disconnect', () => {
        console.warn('Disconnected from backend');
        updateConnectionStatus(false);
    });
    
    socket.on('error', (error) => {
        console.error('Socket.IO error:', error);
        updateConnectionStatus(false);
    });
    
    // Queue events
    socket.on('QueueMemberAdded', (data) => {
        console.info('Queue member added:', data);
        if (window.queueMonitor && data.queue) {
            window.queueMonitor.refreshQueueDetails(data.queue);
        }
    });
    
    socket.on('QueueMemberRemoved', (data) => {
        console.info('Queue member removed:', data);
        if (window.queueMonitor && data.queue) {
            window.queueMonitor.refreshQueueDetails(data.queue);
        }
    });
    
    socket.on('QueueStatusUpdate', (data) => {
        console.info('Queue status update:', data);
        if (window.queueMonitor) {
            window.queueMonitor.refreshQueues();
        }
    });
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    if (connected) {
        connectionStatus.textContent = 'Connected';
        connectionStatus.classList.remove('connection-disconnected');
        connectionStatus.classList.add('connection-connected');
    } else {
        connectionStatus.textContent = 'Disconnected';
        connectionStatus.classList.remove('connection-connected');
        connectionStatus.classList.add('connection-disconnected');
    }
}

// Refresh data
function refreshData() {
    console.info('Refreshing data');
    
    // Show refresh indicator
    refreshIndicator.style.display = 'inline-block';
    
    // Refresh queues
    if (window.queueMonitor) {
        window.queueMonitor.refreshQueues();
        
        // If a queue is being viewed, refresh its details
        if (window.queueMonitor.currentQueueName) {
            window.queueMonitor.refreshQueueDetails(window.queueMonitor.currentQueueName);
        }
    }
    
    // Hide refresh indicator after a short delay
    setTimeout(() => {
        refreshIndicator.style.display = 'none';
    }, 500);
}
