class EndpointMonitor {
    constructor() {
        this.endpoints = [];
        this.endpointsTable = document.getElementById('endpoints-table');
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.noDataAlert = document.getElementById('no-data');
        this.refreshBtn = document.getElementById('refresh-btn');
        this.refreshIndicator = document.getElementById('refresh-indicator');

        // Bind event listeners
        this.refreshBtn.addEventListener('click', () => this.fetchEndpoints());
        
        // Bind event handler methods
        this.handleEvent = this.handleEvent.bind(this);
    }

    // Format the device state display
    formatDeviceState(state) {
        if (!state) return 'Unknown';
        
        // Normalize state string
        state = state.toUpperCase().replace('_', ' ');
        
        let statusColor = '#dc3545'; // Default red (unavailable)
        let displayState = state;
        let stateIcon = '';
        
        if (state === 'NOT INUSE' || state === 'NOT IN USE') {
            statusColor = '#28a745'; // Green
            displayState = 'Available';
            stateIcon = `<i class="bi bi-telephone me-1" style="color: ${statusColor}"></i>`;
        } else if (state === 'UNAVAILABLE') {
            statusColor = '#dc3545'; // Red
            displayState = 'Unavailable';
            stateIcon = `<i class="bi bi-telephone-x me-1" style="color: ${statusColor}"></i>`;
        } else {
            statusColor = '#ffc107'; // Yellow for any other state
            displayState = 'Busy';
            stateIcon = `<i class="bi bi-telephone-minus me-1" style="color: ${statusColor}"></i>`;
        }
        
        return `${stateIcon}<span style="color: ${statusColor}">${displayState}</span>`;
    }

    // Render endpoints table
    renderEndpointsTable() {
        if (this.endpoints.length === 0) {
            this.loadingIndicator.classList.add('d-none');
            this.noDataAlert.classList.remove('d-none');
            return;
        }
        
        this.loadingIndicator.classList.add('d-none');
        this.noDataAlert.classList.add('d-none');
        
        this.endpointsTable.innerHTML = '';
        
        this.endpoints.forEach(endpoint => {
            const row = document.createElement('tr');
            row.classList.add('endpoint-row');
            row.setAttribute('data-extension', endpoint.Extension);
            
            row.innerHTML = `
                <td>${endpoint.Extension}</td>
                <td>${endpoint.Name}</td>
                <td>${this.formatDeviceState(endpoint.State)}</td>
                <td>${endpoint.lastUpdated || formatTimestamp()}</td>
            `;
            
            this.endpointsTable.appendChild(row);
        });
    }

    // Fetch endpoints data from API
    async fetchEndpoints() {
        try {
            this.refreshIndicator.style.display = 'inline-block';
            
            const response = await fetch('/api/endpoints');
            const data = await response.json();
            
            if (data.status === 'success' && Array.isArray(data.endpoints)) {
                // Add timestamp to each endpoint
                this.endpoints = data.endpoints.map(endpoint => ({
                    ...endpoint,
                    lastUpdated: formatTimestamp()
                }));
                this.renderEndpointsTable();
            } else {
                console.error('Failed to fetch endpoints:', data);
                this.noDataAlert.textContent = 'Failed to load endpoint data. Please try again.';
                this.noDataAlert.classList.remove('d-none');
                this.loadingIndicator.classList.add('d-none');
            }
        } catch (error) {
            console.error('Error fetching endpoints:', error);
            this.noDataAlert.textContent = 'Error loading endpoint data: ' + error.message;
            this.noDataAlert.classList.remove('d-none');
            this.loadingIndicator.classList.add('d-none');
        } finally {
            this.refreshIndicator.style.display = 'none';
        }
    }

    // Update endpoint state
    updateEndpointState(deviceName, newState) {
        // Extract extension from device name (format: PJSIP/XXX)
        const extension = deviceName.split('/')[1];
        if (!extension) return;
        
        const endpoint = this.endpoints.find(ep => ep.Extension === extension);
        if (!endpoint) return;
        
        // Update the state
        endpoint.State = newState;
        endpoint.lastUpdated = formatTimestamp();
        
        // Update the UI
        const row = document.querySelector(`tr[data-extension="${extension}"]`);
        if (row) {
            const stateCell = row.cells[2];
            stateCell.innerHTML = this.formatDeviceState(newState);
        }
    }

    // Handle AMI events
    handleEvent(data) {
        const eventType = data.Event;
        this.updateEndpointState(data.Device, data.State);

    }

    // Initialize the monitor
    initialize() {
        this.fetchEndpoints();
    }
}
