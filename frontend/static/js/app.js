// Global instances
let endpointMonitor;
let endpointManager;
let callMonitor;
let socket;

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded, initializing application...');
    
    // Initialize endpoint monitor
    console.log('Creating EndpointMonitor instance');
    endpointMonitor = new EndpointMonitor();
    console.log('EndpointMonitor created:', endpointMonitor);
    endpointMonitor.initialize();
    console.log('EndpointMonitor initialized');
    
    // Make endpointMonitor available globally for debugging
    window.endpointMonitor = endpointMonitor;
    console.log('EndpointMonitor assigned to window.endpointMonitor');
    
    // Initialize endpoint manager
    console.log('Creating EndpointManager instance');
    endpointManager = new EndpointManager();
    console.log('EndpointManager created:', endpointManager);
    endpointManager.initialize();
    console.log('EndpointManager initialized');
    
    // Make endpointManager available globally for debugging
    window.endpointManager = endpointManager;
    console.log('EndpointManager assigned to window.endpointManager');

    // Initialize call monitor
    console.log('Creating CallMonitor instance');
    callMonitor = new CallMonitor();
    callMonitor.initialize();
    console.log('CallMonitor initialized');

    // Initialize socket connection after monitors are ready
    console.log('Initializing socket connection');
    socket = initializeSocketConnection(endpointMonitor, callMonitor);
    console.log('Socket connection initialized');
});