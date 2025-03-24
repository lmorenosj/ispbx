class EndpointMonitor {
    constructor() {
        this.endpoints = [];
        this.endpointsTable = document.getElementById('endpoints-table');
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.noDataAlert = document.getElementById('no-data');
        this.refreshBtn = document.getElementById('refresh-btn');
        this.refreshIndicator = document.getElementById('refresh-indicator');
        this.addEndpointBtn = document.getElementById('addEndpointBtn');

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
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary edit-endpoint-btn" data-extension="${endpoint.Extension}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-endpoint-btn" data-extension="${endpoint.Extension}">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            
            this.endpointsTable.appendChild(row);
        });
    }

    // Fetch endpoints data from API
    async fetchEndpoints(isAutoRefresh = false) {
        try {
            console.log(`Fetching endpoints data... (Auto refresh: ${isAutoRefresh})`);
            console.log('refreshIndicator element:', this.refreshIndicator);
            this.refreshIndicator.style.display = 'inline-block';
            console.log('refreshIndicator display set to inline-block');
            
            console.log('Sending fetch request to /api/endpoints');
            const response = await fetch('/api/endpoints');
            console.log('Response received:', response.status);
            const data = await response.json();
            console.log('Parsed response data:', data);
            
            if (data.status === 'success' && Array.isArray(data.endpoints)) {
                console.log(`Received ${data.endpoints.length} endpoints`);
                // Add timestamp to each endpoint
                this.endpoints = data.endpoints.map(endpoint => ({
                    ...endpoint,
                    lastUpdated: formatTimestamp()
                }));
                console.log('Rendering endpoints table');
                this.renderEndpointsTable();
                console.log('Endpoints table rendered');
                
                if (isAutoRefresh) {
                    console.log('Dashboard automatically refreshed after endpoint operation');
                }
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
            console.log('Setting refreshIndicator display to none');
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
