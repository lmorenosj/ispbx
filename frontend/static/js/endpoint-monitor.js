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
                <td>${endpoint.Extension}</td>
                <td>${endpoint.Name}</td>
                <td>${this.formatEndpointState(endpoint.State)}</td>
                <td>${endpoint.lastUpdated || formatTimestamp()}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-info view-endpoint-btn" data-extension="${endpoint.Extension}">
                            <i class="bi bi-eye"></i> View
                        </button>
                        <button class="btn btn-sm btn-warning update-endpoint-btn" data-extension="${endpoint.Extension}">
                            <i class="bi bi-pencil"></i> Edit
                        </button>
                        <button class="btn btn-sm btn-danger delete-endpoint-btn" data-extension="${endpoint.Extension}">
                            <i class="bi bi-trash"></i> Delete
                        </button>
                    </div>
                </td>
            `;
            
            this.endpointsTable.appendChild(row);
        });

        // Add event listeners to the view buttons
        document.querySelectorAll('.view-endpoint-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const extension = e.currentTarget.getAttribute('data-extension');
                this.showEndpointDetails(extension);
            });
        });

        // Add event listeners to the update buttons
        document.querySelectorAll('.update-endpoint-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const extension = e.currentTarget.getAttribute('data-extension');
                this.showEndpointForm('update', extension);
            });
        });
        
        // Add event listeners to the delete buttons
        document.querySelectorAll('.delete-endpoint-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const extension = e.currentTarget.getAttribute('data-extension');
                this.confirmDeleteEndpoint(extension);
            });
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
        // Extract extension from endpoint name (format: PJSIP/XXX)
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
    }

    // Handle AMI events
    handleEvent(data) {
        const eventType = data.Event;
        this.updateEndpointState(data.Device, data.State);

    }

    // Fetch and display endpoint details
    async showEndpointDetails(extension) {
        try {
            // Get the modal element from the template
            const detailsModal = document.getElementById('endpoint-details-modal');
            
            // Get modal elements
            const modalExtensionNumber = document.getElementById('modal-extension-number');
            const endpointDetailsLoading = document.getElementById('endpoint-details-loading');
            const endpointDetailsContent = document.getElementById('endpoint-details-content');
            const endpointDetailsJson = document.getElementById('endpoint-details-json');
            const endpointDetailsError = document.getElementById('endpoint-details-error');
            
            // Reset modal content
            modalExtensionNumber.textContent = extension;
            endpointDetailsLoading.classList.remove('d-none');
            endpointDetailsContent.classList.add('d-none');
            endpointDetailsError.classList.add('d-none');
            
            // Show the modal
            const modal = new bootstrap.Modal(detailsModal);
            modal.show();
            
            // Fetch endpoint details
            const response = await fetch(`/api/endpoints/${extension}`);
            const data = await response.json();
            
            // Hide loading indicator
            endpointDetailsLoading.classList.add('d-none');
            
            if (data.status === 'success') {
                // Display endpoint details
                endpointDetailsContent.classList.remove('d-none');
                
                // Display detailed info if available
                if (data.details) {
                    // Create a table for the details object
                    const detailsTable = document.createElement('table');
                    detailsTable.className = 'table table-bordered';
                    
                    // Add rows for each property in the details object
                    Object.entries(data.details).forEach(([key, value]) => {
                        const row = document.createElement('tr');
                        
                        const headerCell = document.createElement('th');
                        headerCell.textContent = key;
                        row.appendChild(headerCell);
                        
                        const valueCell = document.createElement('td');
                        valueCell.textContent = value || 'N/A';
                        row.appendChild(valueCell);
                        
                        detailsTable.appendChild(row);
                    });
                    
                    // Clear previous content and add the table
                    endpointDetailsJson.innerHTML = '';
                    endpointDetailsJson.appendChild(detailsTable);
                } else {
                    endpointDetailsJson.textContent = 'No detailed information available';
                }
            } else {
                // Show error
                endpointDetailsError.textContent = 'Failed to load endpoint details: ' + (data.message || 'Unknown error');
                endpointDetailsError.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Error fetching endpoint details:', error);
            
            // Get error elements and show error
            const endpointDetailsLoading = document.getElementById('endpoint-details-loading');
            const endpointDetailsError = document.getElementById('endpoint-details-error');
            
            endpointDetailsLoading.classList.add('d-none');
            endpointDetailsError.textContent = 'Error loading endpoint details: ' + error.message;
            endpointDetailsError.classList.remove('d-none');
        }
    }

    // Show endpoint form for create or update
    async showEndpointForm(mode, extension = null) {
        // Get the modal element
        const formModal = document.getElementById('endpoint-form-modal');
        const formTitle = document.getElementById('endpoint-form-title');
        const formMode = document.getElementById('form-mode');
        const extensionField = document.getElementById('form-extension');
        const extensionFieldContainer = document.getElementById('extension-field-container');
        const extensionOriginal = document.getElementById('form-extension-original');
        const nameField = document.getElementById('form-name');
        const passwordField = document.getElementById('form-password');
        const contextField = document.getElementById('form-context');
        const formLoading = document.getElementById('endpoint-form-loading');
        const formError = document.getElementById('endpoint-form-error');
        const formSuccess = document.getElementById('endpoint-form-success');
        const formSubmitBtn = document.getElementById('endpoint-form-submit');
        
        // Reset form
        document.getElementById('endpoint-form').reset();
        formError.classList.add('d-none');
        formSuccess.classList.add('d-none');
        formLoading.classList.add('d-none');
        
        // Set form mode
        formMode.value = mode;
        
        if (mode === 'create') {
            // Configure form for create mode
            formTitle.textContent = 'Add New Endpoint';
            extensionFieldContainer.classList.remove('d-none');
            extensionField.removeAttribute('disabled');
            extensionField.value = '';
            extensionOriginal.value = '';
            nameField.value = '';
            passwordField.value = '';
            contextField.value = 'from-internal';
        } else if (mode === 'update' && extension) {
            // Configure form for update mode
            formTitle.textContent = `Update Endpoint ${extension}`;
            extensionFieldContainer.classList.add('d-none');
            extensionField.setAttribute('disabled', 'disabled');
            extensionField.value = extension;
            extensionOriginal.value = extension;
            
            // Show loading
            formLoading.classList.remove('d-none');
            
            try {
                // Fetch endpoint configuration from the new API endpoint
                const response = await fetch(`/api/endpoints/${extension}/config`);
                const data = await response.json();
                
                // Hide loading
                formLoading.classList.add('d-none');
                
                if (data.status === 'success') {
                    // Populate form with endpoint configuration
                    const config = data.config || {};
                    const endpointConfig = config.endpoint || {};
                    const authConfig = config.auth || {};
                    
                    // Set form values from the configuration
                    // Extract name from callerid if available (format: "user107 <107>")
                    let name = '';
                    const callerid = endpointConfig.callerid || '';
                    const callerIdMatch = callerid.match(/^([^<]+)/);
                    if (callerIdMatch && callerIdMatch[1]) {
                        name = callerIdMatch[1].trim();
                    }
                    
                    nameField.value = name;
                    
                    // Password handling
                    passwordField.value = '';
                    passwordField.placeholder = 'Leave blank to keep current password';
                    passwordField.required = false;
                    
                    // Set other fields from the configuration
                    contextField.value = endpointConfig.context || 'from-internal';
                } else {
                    // Show error
                    formError.textContent = 'Failed to load endpoint details: ' + (data.message || 'Unknown error');
                    formError.classList.remove('d-none');
                }
            } catch (error) {
                console.error('Error fetching endpoint details:', error);
                formLoading.classList.add('d-none');
                formError.textContent = 'Error loading endpoint details: ' + error.message;
                formError.classList.remove('d-none');
            }
        }
        
        // Show the modal
        const modal = new bootstrap.Modal(formModal);
        modal.show();
        
        // Set up form submit handler
        formSubmitBtn.onclick = async () => {
            // Validate form
            const form = document.getElementById('endpoint-form');
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            
            // Show loading
            formLoading.classList.remove('d-none');
            formError.classList.add('d-none');
            formSuccess.classList.add('d-none');
            
            try {
                // Prepare endpoint data
                const endpointData = {
                    extension: extensionField.value,
                    name: nameField.value,
                    context: contextField.value
                };
                
                // Only include password if it's not empty
                if (passwordField.value) {
                    endpointData.password = passwordField.value;
                }
                
                let response;
                
                if (mode === 'create') {
                    // Create new endpoint
                    response = await fetch('/api/endpoints', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(endpointData)
                    });
                } else if (mode === 'update') {
                    // Update existing endpoint
                    response = await fetch(`/api/endpoints/${extensionOriginal.value}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(endpointData)
                    });
                }
                
                // Check if response is ok before parsing JSON
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                
                // Check content type to ensure it's JSON
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Response is not JSON');
                }
                
                const data = await response.json();
                
                // Hide loading
                formLoading.classList.add('d-none');
                
                if (data.status === 'success') {
                    // Show success message
                    formSuccess.textContent = data.message || 'Operation completed successfully';
                    formSuccess.classList.remove('d-none');
                    
                    // Refresh endpoints list after a short delay
                    setTimeout(() => {
                        this.fetchEndpoints();
                        // Close the modal
                        bootstrap.Modal.getInstance(formModal).hide();
                    }, 1500);
                } else {
                    // Show error
                    formError.textContent = data.message || 'Operation failed';
                    formError.classList.remove('d-none');
                }
            } catch (error) {
                console.error('Error submitting endpoint form:', error);
                formLoading.classList.add('d-none');
                formError.textContent = 'Error: ' + error.message;
                formError.classList.remove('d-none');
            }
        };
    }

    // Confirm delete endpoint
    async confirmDeleteEndpoint(extension) {
        // Get the modal element
        const deleteModal = document.getElementById('endpoint-delete-modal');
        const deleteExtensionNumber = document.getElementById('delete-extension-number');
        const deleteExtensionField = document.getElementById('delete-extension');
        const deleteLoading = document.getElementById('endpoint-delete-loading');
        const deleteError = document.getElementById('endpoint-delete-error');
        const deleteSuccess = document.getElementById('endpoint-delete-success');
        const deleteConfirmBtn = document.getElementById('endpoint-delete-confirm');
        
        // Reset modal
        deleteError.classList.add('d-none');
        deleteSuccess.classList.add('d-none');
        deleteLoading.classList.add('d-none');
        
        // Set extension
        deleteExtensionNumber.textContent = extension;
        deleteExtensionField.value = extension;
        
        // Show the modal
        const modal = new bootstrap.Modal(deleteModal);
        modal.show();
        
        // Set up confirm button handler
        deleteConfirmBtn.onclick = async () => {
            // Show loading
            deleteLoading.classList.remove('d-none');
            deleteError.classList.add('d-none');
            deleteSuccess.classList.add('d-none');
            
            try {
                await this.deleteEndpoint(extension);
                
                // Hide loading
                deleteLoading.classList.add('d-none');
                
                // Show success message
                deleteSuccess.textContent = `Endpoint ${extension} has been deleted successfully.`;
                deleteSuccess.classList.remove('d-none');
                
                // Refresh endpoints list after a short delay
                setTimeout(() => {
                    this.fetchEndpoints();
                    // Close the modal
                    bootstrap.Modal.getInstance(deleteModal).hide();
                }, 1500);
            } catch (error) {
                console.error('Error deleting endpoint:', error);
                deleteLoading.classList.add('d-none');
                deleteError.textContent = 'Error deleting endpoint: ' + error.message;
                deleteError.classList.remove('d-none');
            }
        };
    }
    
    // Delete endpoint
    async deleteEndpoint(extension) {
        // Send DELETE request to API
        const response = await fetch(`/api/endpoints/${extension}`, {
            method: 'DELETE'
        });
        
        // Check if response is ok before parsing JSON
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        // Check content type to ensure it's JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Response is not JSON');
        }
        
        const data = await response.json();
        
        if (data.status !== 'success') {
            throw new Error(data.message || 'Failed to delete endpoint');
        }
        
        return data;
    }
    
    // Initialize the monitor
    initialize() {
        this.fetchEndpoints();
        
        // Add event listener for the add endpoint button
        const addEndpointBtn = document.getElementById('add-endpoint-btn');
        if (addEndpointBtn) {
            addEndpointBtn.addEventListener('click', () => {
                this.showEndpointForm('create');
            });
        }
    }
}
