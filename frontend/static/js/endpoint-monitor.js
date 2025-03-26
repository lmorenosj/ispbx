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
        
        console.info('EndpointMonitor initialized with consistent endpoint terminology');
    }

    // Format the endpoint state display
    formatEndpointState(state) {
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
                <td>
                    <a href="/endpoint?extension=${endpoint.Extension}" class="text-decoration-none" target="_blank">
                        ${endpoint.Extension}
                    </a>
                </td>
                <td>${endpoint.Name}</td>
                <td>${this.formatEndpointState(endpoint.State)}</td>
                <td>${endpoint.lastUpdated || formatTimestamp()}</td>
                <td class="text-end">
                    <a href="/endpoint?extension=${endpoint.Extension}" class="btn btn-sm btn-outline-info me-1" title="View Dashboard" target="_blank">
                        <i class="bi bi-graph-up"></i>
                    </a>
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
        
        console.debug(`Rendered endpoints table with ${this.endpoints.length} endpoints`);
    }

    // Fetch endpoints data directly from backend API
    async fetchEndpoints(isAutoRefresh = false) {
        try {
            console.info(`Fetching endpoints data from backend... (Auto refresh: ${isAutoRefresh})`);
            console.debug('refreshIndicator element:', this.refreshIndicator);
            this.refreshIndicator.style.display = 'inline-block';
            console.debug('refreshIndicator display set to inline-block');
            
            console.info(`Sending fetch request to ${API_CONFIG.BACKEND_URL}${API_CONFIG.ENDPOINTS.LIST}`);
            try {
                const { status, data } = await fetchAPI(API_CONFIG.ENDPOINTS.LIST);
                console.debug('Response status:', status);
                console.debug('Parsed response data:', data);
                
                if (data.status === 'success' && Array.isArray(data.endpoints)) {
                    console.info(`Received ${data.endpoints.length} endpoints`);
                    // Add timestamp to each endpoint
                    this.endpoints = data.endpoints.map(endpoint => ({
                        ...endpoint,
                        lastUpdated: formatTimestamp()
                    }));
                    console.debug('Rendering endpoints table');
                    this.renderEndpointsTable();
                    console.debug('Endpoints table rendered');
                    
                    if (isAutoRefresh) {
                        console.info('Dashboard automatically refreshed after endpoint operation');
                    }
                } else {
                    console.error('Failed to fetch endpoints:', data);
                    this.noDataAlert.textContent = 'Failed to load endpoint data. Please try again.';
                    this.noDataAlert.classList.remove('d-none');
                    this.loadingIndicator.classList.add('d-none');
                }
            } catch (apiError) {
                console.error('API error fetching endpoints:', apiError);
                this.noDataAlert.textContent = 'Error loading endpoint data: ' + apiError.message;
                this.noDataAlert.classList.remove('d-none');
                this.loadingIndicator.classList.add('d-none');
            }
        } catch (error) {
            console.error('Error in fetchEndpoints:', error);
            this.noDataAlert.textContent = 'Error loading endpoint data: ' + error.message;
            this.noDataAlert.classList.remove('d-none');
            this.loadingIndicator.classList.add('d-none');
        } finally {
            console.debug('Setting refreshIndicator display to none');
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
            stateCell.innerHTML = this.formatEndpointState(newState);
        }
        
        console.debug(`Updated endpoint ${extension} state to ${newState}`);
    }

    // Process events with consistent endpoint terminology
    handleEvent(data) {
        // Check if this is a device state event
        if (data.Device && data.State) {
            console.debug(`Processing endpoint state event for ${data.Device}: ${data.State}`);
            this.updateEndpointState(data.Device, data.State);
        } else {
            console.warn('Received event with unexpected format:', data);
        }
    }

    // Initialize the monitor
    initialize() {
        this.fetchEndpoints();
    }
}
