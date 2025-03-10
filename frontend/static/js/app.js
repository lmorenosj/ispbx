document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const endpointsTable = document.getElementById('endpoints-table');
    const loadingIndicator = document.getElementById('loading-indicator');
    const noDataAlert = document.getElementById('no-data');
    const refreshBtn = document.getElementById('refresh-btn');
    const refreshIndicator = document.getElementById('refresh-indicator');
    const connectionStatus = document.getElementById('connection-status');
    
    // Store endpoints data
    let endpoints = [];
    
    // Format the state display
    function formatState(state) {
        if (!state) return 'Unknown';
        
        // Normalize state string
        state = state.toUpperCase().replace('_', ' ');
        
        let statusClass = 'status-unavailable';
        if (state === 'NOT INUSE' || state === 'NOT IN USE') {
            statusClass = 'status-not-in-use';
            state = 'Not In Use';
        } else if (state === 'BUSY' || state.includes('IN USE')) {
            statusClass = 'status-busy';
        } else if (state === 'UNAVAILABLE') {
            state = 'Unavailable';
        }
        
        return `<span class="status-indicator ${statusClass}"></span>${state}`;
    }
    
    // Format timestamp
    function formatTimestamp(timestamp) {
        return new Date().toLocaleTimeString();
    }
    
    // Render endpoints table
    function renderEndpointsTable() {
        if (endpoints.length === 0) {
            loadingIndicator.classList.add('d-none');
            noDataAlert.classList.remove('d-none');
            return;
        }
        
        loadingIndicator.classList.add('d-none');
        noDataAlert.classList.add('d-none');
        
        endpointsTable.innerHTML = '';
        
        endpoints.forEach(endpoint => {
            const row = document.createElement('tr');
            row.classList.add('endpoint-row');
            row.setAttribute('data-extension', endpoint.Extension);
            
            row.innerHTML = `
                <td>${endpoint.Extension}</td>
                <td>${endpoint.Name}</td>
                <td>${formatState(endpoint.State)}</td>
                <td>${endpoint.lastUpdated || formatTimestamp()}</td>
            `;
            
            endpointsTable.appendChild(row);
        });
    }
    
    // Fetch endpoints data from API
    async function fetchEndpoints() {
        try {
            refreshIndicator.style.display = 'inline-block';
            
            const response = await fetch('/api/endpoints');
            const data = await response.json();
            
            if (data.status === 'success' && Array.isArray(data.endpoints)) {
                // Add timestamp to each endpoint
                endpoints = data.endpoints.map(endpoint => ({
                    ...endpoint,
                    lastUpdated: formatTimestamp()
                }));
                renderEndpointsTable();
            } else {
                console.error('Failed to fetch endpoints:', data);
                noDataAlert.textContent = 'Failed to load endpoint data. Please try again.';
                noDataAlert.classList.remove('d-none');
                loadingIndicator.classList.add('d-none');
            }
        } catch (error) {
            console.error('Error fetching endpoints:', error);
            noDataAlert.textContent = 'Error loading endpoint data: ' + error.message;
            noDataAlert.classList.remove('d-none');
            loadingIndicator.classList.add('d-none');
        } finally {
            refreshIndicator.style.display = 'none';
        }
    }
    
    // Update endpoint state
    function updateEndpointState(deviceName, newState) {
        // Extract extension from device name (format: PJSIP/XXX)
        const extension = deviceName.split('/')[1];
        if (!extension) return;
        
        // Find the endpoint in our data
        const endpoint = endpoints.find(ep => ep.Extension === extension);
        
        if (endpoint) {
            endpoint.State = newState;
            endpoint.lastUpdated = formatTimestamp();
            
            // Update the specific table row
            const row = document.querySelector(`tr[data-extension="${extension}"]`);
            if (row) {
                const stateCell = row.cells[2];
                const timestampCell = row.cells[3];
                
                stateCell.innerHTML = formatState(newState);
                timestampCell.textContent = endpoint.lastUpdated;
                
                // Highlight the updated row
                row.classList.remove('updated');
                void row.offsetWidth; // Trigger reflow to restart animation
                row.classList.add('updated');
            } else {
                // If row doesn't exist, re-render the table
                renderEndpointsTable();
            }
        } else {
            // If endpoint not found, refresh the entire table
            fetchEndpoints();
        }
    }
    
    // Initialize Socket.IO connection
    function initializeSocketConnection() {
        // Connect to the Socket.IO server
        connectionStatus.textContent = 'Connecting...';
        connectionStatus.className = 'connection-status connection-disconnected';
        
        // We're assuming the Socket.IO server is at the same host as this page
        const socket = io();
        
        socket.on('connect', () => {
            console.log('Connected to Socket.IO server');
            connectionStatus.textContent = 'Connected';
            connectionStatus.className = 'connection-status connection-connected';
        });
        
        socket.on('disconnect', () => {
            console.log('Disconnected from Socket.IO server');
            connectionStatus.textContent = 'Disconnected';
            connectionStatus.className = 'connection-status connection-disconnected';
        });
        
        socket.on('DeviceStateChange', (data) => {
            console.log('DeviceStateChange event received:', data);
            if (data && data.data) {
                const eventData = data.data;
                updateEndpointState(eventData.Device, eventData.State);
            }
        });
        
        // Error handling
        socket.on('connect_error', (error) => {
            console.error('Socket.IO connection error:', error);
            connectionStatus.textContent = 'Connection Error';
            connectionStatus.className = 'connection-status connection-disconnected';
        });
        
        return socket;
    }
    
    // Event listeners
    refreshBtn.addEventListener('click', fetchEndpoints);
    
    // Initialize the application
    fetchEndpoints();
    const socket = initializeSocketConnection();
    
    // Poll for updates every 30 seconds as a fallback
    //
    // 
    // setInterval(fetchEndpoints, 30000);
});