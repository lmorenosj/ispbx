class EndpointDashboard {
    constructor() {
        // DOM elements
        this.endpointId = document.getElementById('endpoint-id');
        this.endpointName = document.getElementById('endpoint-name');
        this.endpointExtension = document.getElementById('endpoint-extension');
        this.endpointContext = document.getElementById('endpoint-context');
        this.endpointStatus = document.getElementById('endpoint-status');
        this.endpointLastRegistered = document.getElementById('endpoint-last-registered');
        this.endpointCodecs = document.getElementById('endpoint-codecs');
        this.endpointStateIndicator = document.getElementById('endpoint-state-indicator');
        
        // Statistics elements
        this.endpointUptime = document.getElementById('endpoint-uptime');
        this.endpointLatency = document.getElementById('endpoint-latency');
        this.endpointTodayCalls = document.getElementById('endpoint-today-calls');
        this.endpointTalkTime = document.getElementById('endpoint-talk-time');
        
        // Call elements
        this.recentCallsTable = document.getElementById('recent-calls-table');
        this.noRecentCalls = document.getElementById('no-recent-calls');
        
        // UI elements
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.noData = document.getElementById('no-data');
        this.endpointDetails = document.getElementById('endpoint-details');
        this.refreshBtn = document.getElementById('refresh-btn');
        this.refreshIndicator = document.getElementById('refresh-indicator');
        this.editEndpointBtn = document.getElementById('editEndpointBtn');
        this.backToListBtn = document.getElementById('backToListBtn');
        
        // Data
        this.endpoint = null;
        this.recentCalls = [];
        this.extension = this.getExtensionFromUrl();
        
        // Bind event handlers
        this.refreshBtn.addEventListener('click', () => this.fetchEndpointData());
        this.editEndpointBtn.addEventListener('click', () => this.showEditModal());
        this.backToListBtn.addEventListener('click', () => window.location.href = '/');
        
        // Bind event handler methods
        this.handleEvent = this.handleEvent.bind(this);
        
        console.info('EndpointDashboard initialized');
    }
    
    // Get extension from URL query parameter
    getExtensionFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('extension');
    }
    
    // Initialize the dashboard
    initialize() {
        if (!this.extension) {
            this.showError('No extension specified');
            return;
        }
        
        this.fetchEndpointData();
    }
    
    // Show error message
    showError(message) {
        this.loadingIndicator.classList.add('d-none');
        this.endpointDetails.classList.add('d-none');
        this.noData.textContent = message;
        this.noData.classList.remove('d-none');
    }
    
    // Format endpoint state display with icon
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
    
    // Fetch endpoint data from backend
    async fetchEndpointData() {
        try {
            console.info(`Fetching endpoint data for extension ${this.extension}`);
            this.refreshIndicator.style.display = 'inline-block';
            this.loadingIndicator.classList.remove('d-none');
            this.endpointDetails.classList.add('d-none');
            this.noData.classList.add('d-none');
            
            // Fetch endpoint details
            const { status, data } = await fetchAPI(API_CONFIG.ENDPOINTS.DB_GET(this.extension));
            
            if (data.status === 'success' && data.endpoint) {
                console.info(`Received endpoint data for ${this.extension}`);
                this.endpoint = data.endpoint;
                this.renderEndpointDetails();
                
                // Fetch recent calls for this endpoint
                this.fetchRecentCalls();
            } else {
                console.error('Failed to fetch endpoint details:', data);
                this.showError('Failed to load endpoint details. Please try again.');
            }
        } catch (error) {
            console.error('Error in fetchEndpointData:', error);
            this.showError('Error loading endpoint data: ' + error.message);
        } finally {
            this.refreshIndicator.style.display = 'none';
            this.loadingIndicator.classList.add('d-none');
        }
    }
    
    // Render endpoint details
    renderEndpointDetails() {
        if (!this.endpoint) return;
        
        const endpoint = this.endpoint.endpoint;
        const aor = this.endpoint.aor;
        
        // Extract name from callerid (format: "Name" <extension>)
        const callerid = endpoint.callerid || '';
        const nameMatch = callerid.match(/"([^"]+)"/);
        const name = nameMatch ? nameMatch[1] : this.extension;
        
        // Update basic info
        this.endpointId.textContent = this.extension;
        this.endpointName.textContent = name;
        this.endpointExtension.textContent = this.extension;
        this.endpointContext.textContent = endpoint.context || 'from-internal';
        
        // Update status with icon
        const state = 'NOT INUSE'; // Default state, will be updated by events
        this.endpointStatus.innerHTML = this.formatEndpointState(state);
        this.endpointStateIndicator.innerHTML = this.formatEndpointState(state);
        
        // Update last registered (placeholder for now)
        this.endpointLastRegistered.textContent = new Date().toLocaleString();
        
        // Update codecs
        const allowedCodecs = (endpoint.allow || '').split(',');
        this.endpointCodecs.textContent = allowedCodecs.join(', ');
        
        // Update statistics (placeholders for now)
        this.endpointUptime.textContent = '00:00:00';
        this.endpointLatency.textContent = '0 ms';
        this.endpointTodayCalls.textContent = '0';
        this.endpointTalkTime.textContent = '00:00:00';
        
        // Show endpoint details
        this.endpointDetails.classList.remove('d-none');
        
        // Set up edit button
        this.editEndpointBtn.setAttribute('data-extension', this.extension);
    }
    
    // Fetch recent calls for this endpoint
    async fetchRecentCalls() {
        try {
            // This is a placeholder - in a real implementation, you would fetch from CDR API
            // For now, we'll use mock data
            this.recentCalls = [
                {
                    datetime: new Date(Date.now() - 3600000).toLocaleString(),
                    direction: 'Outgoing',
                    peer: '2000',
                    duration: '00:05:23',
                    status: 'Completed'
                },
                {
                    datetime: new Date(Date.now() - 7200000).toLocaleString(),
                    direction: 'Incoming',
                    peer: '3000',
                    duration: '00:02:45',
                    status: 'Completed'
                },
                {
                    datetime: new Date(Date.now() - 86400000).toLocaleString(),
                    direction: 'Outgoing',
                    peer: '2001',
                    duration: '00:00:15',
                    status: 'No Answer'
                }
            ];
            
            this.renderRecentCalls();
        } catch (error) {
            console.error('Error fetching recent calls:', error);
        }
    }
    
    // Render recent calls table
    renderRecentCalls() {
        this.recentCallsTable.innerHTML = '';
        
        if (this.recentCalls.length === 0) {
            this.noRecentCalls.classList.remove('d-none');
            return;
        }
        
        this.noRecentCalls.classList.add('d-none');
        
        this.recentCalls.forEach(call => {
            const row = document.createElement('tr');
            
            row.innerHTML = `
                <td>${call.datetime}</td>
                <td>${call.direction}</td>
                <td>${call.peer}</td>
                <td>${call.duration}</td>
                <td>${call.status}</td>
            `;
            
            this.recentCallsTable.appendChild(row);
        });
    }
    

    
    // Show edit modal for this endpoint
    showEditModal() {
        // Get the EndpointManager instance from the global scope
        const endpointManager = window.endpointManager;
        
        if (endpointManager) {
            endpointManager.showEditEndpointModal(this.extension);
        } else {
            console.error('EndpointManager not found');
            
            // Create a new instance if not available
            window.endpointManager = new EndpointManager();
            window.endpointManager.initialize();
            window.endpointManager.showEditEndpointModal(this.extension);
        }
    }
    
    // Handle events from Socket.IO
    handleEvent(data) {
        // Check if this is a device state event for our endpoint
        if (data.Device && data.State) {
            // Extract extension from device name (format: PJSIP/XXX)
            const deviceParts = data.Device.split('/');
            if (deviceParts.length < 2) return;
            
            const extension = deviceParts[1];
            
            // Only process events for this endpoint
            if (extension !== this.extension) return;
            
            console.debug(`Processing endpoint state event for ${extension}: ${data.State}`);
            
            // Update the status display
            this.endpointStatus.innerHTML = this.formatEndpointState(data.State);
            this.endpointStateIndicator.innerHTML = this.formatEndpointState(data.State);
        }
        
        // Check for call events involving this endpoint
        // This would be implemented in a real application to track active calls
    }
}

// Initialize the dashboard when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Create dashboard instance
    window.endpointDashboard = new EndpointDashboard();
    
    // Create endpoint manager instance for edit functionality
    window.endpointManager = new EndpointManager();
    window.endpointManager.initialize();
    
    // Initialize dashboard
    window.endpointDashboard.initialize();
    
    // Initialize Socket.IO connection
    const socket = initializeSocketConnection(window.endpointDashboard, null);
});
