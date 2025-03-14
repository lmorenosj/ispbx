// Global instances
let endpointMonitor;
let callMonitor;
let socket;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize endpoint monitor
    endpointMonitor = new EndpointMonitor();
    endpointMonitor.initialize();

    // Initialize call monitor
    callMonitor = new CallMonitor();
    callMonitor.initialize();

    // Initialize socket connection after monitors are ready
    socket = initializeSocketConnection(endpointMonitor, callMonitor);
});