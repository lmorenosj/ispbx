class EndpointManager {
    constructor() {
        // Modal elements
        this.endpointModal = new bootstrap.Modal(document.getElementById('endpointModal'));
        this.deleteModal = new bootstrap.Modal(document.getElementById('deleteEndpointModal'));
        
        // Form elements
        this.endpointForm = document.getElementById('endpointForm');
        this.endpointAction = document.getElementById('endpointAction');
        this.endpointId = document.getElementById('endpointId');
        this.endpointName = document.getElementById('endpointName');
        this.endpointPassword = document.getElementById('endpointPassword');
        this.endpointContext = document.getElementById('endpointContext');
        this.codecG722 = document.getElementById('codecG722');
        this.codecUlaw = document.getElementById('codecUlaw');
        this.codecAlaw = document.getElementById('codecAlaw');
        this.formError = document.getElementById('endpointFormError');
        
        // Buttons
        this.saveEndpointBtn = document.getElementById('saveEndpointBtn');
        this.confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        this.deleteEndpointId = document.getElementById('deleteEndpointId');
        
        // Reference to the refresh button and indicator
        this.refreshBtn = document.getElementById('refresh-btn');
        this.refreshIndicator = document.getElementById('refresh-indicator');
        
        // Bind event handlers
        this.saveEndpointBtn.addEventListener('click', () => this.saveEndpoint());
        this.confirmDeleteBtn.addEventListener('click', () => this.deleteEndpoint());
    }
    
    // Initialize the endpoint manager
    initialize() {
        console.log('Initializing EndpointManager');
        
        // Add event listeners for the add, edit, and delete buttons
        document.addEventListener('click', (event) => {
            console.log('Click event detected:', event.target);
            
            // Add endpoint button
            if (event.target.matches('#addEndpointBtn') || event.target.closest('#addEndpointBtn')) {
                console.log('Add endpoint button clicked');
                this.showAddEndpointModal();
                return;
            }
            
            // Edit endpoint button - handle both the button and the icon inside it
            const editButton = event.target.matches('.edit-endpoint-btn') ? 
                event.target : event.target.closest('.edit-endpoint-btn');
                
            if (editButton) {
                const extension = editButton.getAttribute('data-extension');
                console.log('Edit button clicked for extension:', extension);
                this.showEditEndpointModal(extension);
                return;
            }
            
            // Delete endpoint button - handle both the button and the icon inside it
            const deleteButton = event.target.matches('.delete-endpoint-btn') ? 
                event.target : event.target.closest('.delete-endpoint-btn');
                
            if (deleteButton) {
                const extension = deleteButton.getAttribute('data-extension');
                console.log('Delete button clicked for extension:', extension);
                this.showDeleteEndpointModal(extension);
                return;
            }
        });
    }
    
    // Show modal for adding a new endpoint
    showAddEndpointModal() {
        // Reset form
        this.endpointForm.reset();
        this.formError.classList.add('d-none');
        
        // Set action to create
        this.endpointAction.value = 'create';
        
        // Enable endpoint ID field
        this.endpointId.disabled = false;
        
        // Set default values
        this.endpointContext.value = 'from-internal';
        this.codecG722.checked = true;
        this.codecUlaw.checked = false;
        this.codecAlaw.checked = false;
        
        // Update modal title
        document.getElementById('endpointModalLabel').textContent = 'Add New Endpoint';
        
        // Show modal
        this.endpointModal.show();
    }
    
    // Show modal for editing an existing endpoint
    async showEditEndpointModal(extension) {
        try {
            console.log(`Showing edit modal for extension ${extension}`);
            
            // Reset form and show loading state
            this.endpointForm.reset();
            this.formError.classList.add('d-none');
            
            // Set action to update
            this.endpointAction.value = 'update';
            
            // Update modal title
            document.getElementById('endpointModalLabel').textContent = 'Edit Endpoint';
            
            // Pre-fill the extension ID and disable it
            this.endpointId.value = extension;
            this.endpointId.disabled = true; // Can't change the extension
            
            // Don't fill password field for security reasons
            this.endpointPassword.value = '';
            this.endpointPassword.placeholder = '(unchanged)';
            this.endpointPassword.required = false;
            
            // Show the modal immediately to provide feedback to the user
            this.endpointModal.show();
            
            // Fetch endpoint details
            console.log(`Fetching details for extension ${extension}`);
            const response = await fetch(`/api/endpoints/db/${extension}`);
            const data = await response.json();
            console.log('Endpoint data received:', data);
            
            if (data.status === 'success' && data.endpoint) {
                const endpoint = data.endpoint;
                
                // Extract name from callerid (format: "Name" <extension>)
                const callerid = endpoint.endpoint.callerid || '';
                const nameMatch = callerid.match(/"([^"]+)"/); 
                this.endpointName.value = nameMatch ? nameMatch[1] : '';
                
                // Set context
                this.endpointContext.value = endpoint.endpoint.context || 'from-internal';
                
                // Set codecs
                const allowedCodecs = (endpoint.endpoint.allow || '').split(',');
                this.codecG722.checked = allowedCodecs.includes('g722');
                this.codecUlaw.checked = allowedCodecs.includes('ulaw');
                this.codecAlaw.checked = allowedCodecs.includes('alaw');
            } else {
                console.error('Failed to fetch endpoint details:', data);
                this.formError.textContent = 'Failed to load endpoint details. Please try again.';
                this.formError.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Error fetching endpoint details:', error);
            this.formError.textContent = 'Error loading endpoint details: ' + error.message;
            this.formError.classList.remove('d-none');
        }
    }
    
    // Show confirmation modal for deleting an endpoint
    showDeleteEndpointModal(extension) {
        this.deleteEndpointId.textContent = extension;
        this.confirmDeleteBtn.setAttribute('data-extension', extension);
        this.deleteModal.show();
    }
    
    // Save endpoint (create or update)
    async saveEndpoint() {
        console.log('saveEndpoint method called');
        try {
            // Validate form
            if (!this.validateForm()) {
                console.log('Form validation failed');
                return;
            }
            console.log('Form validation passed');
            
            // Get form values
            const endpointId = this.endpointId.value.trim();
            const name = this.endpointName.value.trim();
            const password = this.endpointPassword.value.trim();
            const context = this.endpointContext.value.trim();
            
            // Get selected codecs
            const codecs = [];
            if (this.codecG722.checked) codecs.push('g722');
            if (this.codecUlaw.checked) codecs.push('ulaw');
            if (this.codecAlaw.checked) codecs.push('alaw');
            
            // Prepare request payload
            const payload = {
                name,
                context,
                codecs
            };
            
            // Only include password if it's a new endpoint or if it's been changed
            if (this.endpointAction.value === 'create' || password) {
                payload.password = password;
            }
            
            // Add qualify parameters
            payload.qualify_frequency = 60; // Default to 60 seconds
            payload.qualify_timeout = 5;   // Default to 5 seconds
            
            // Determine request method and URL
            let url = '/api/endpoints';
            let method = 'POST';
            
            if (this.endpointAction.value === 'update') {
                url = `/api/endpoints/${endpointId}`;
                method = 'PUT';
            } else if (this.endpointAction.value === 'create') {
                // For creation, we need to include endpoint_id in the payload
                payload.endpoint_id = endpointId;
            }
            
            // Show loading state on refresh button
            if (this.refreshIndicator) {
                console.log('Setting refresh indicator to visible');
                this.refreshIndicator.style.display = 'inline-block';
            } else {
                console.error('Refresh indicator not found');
            }
            
            // Send request
            console.log(`Sending ${method} request to ${url} with payload:`, payload);
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            console.log(`Response status: ${response.status}`);
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.status === 'success') {
                console.log('Operation successful, closing modal');
                // Close modal
                this.endpointModal.hide();
                
                // Refresh endpoints by simulating a click on the refresh button
                console.log(`Refreshing dashboard after ${this.endpointAction.value} operation for endpoint ${endpointId}`);
                // Add a small delay to ensure AMI has time to process the changes
                setTimeout(() => {
                    console.log('Timeout completed, triggering refresh button click');
                    if (this.refreshBtn) {
                        console.log('Clicking refresh button');
                        this.refreshBtn.click();
                    } else {
                        console.error('Refresh button not found');
                    }
                }, 500);
                
                // Show success message
                alert(`Endpoint ${endpointId} ${this.endpointAction.value === 'create' ? 'created' : 'updated'} successfully.`);
            } else {
                // Hide loading state on refresh button
                if (this.refreshIndicator) {
                    console.log('Setting refresh indicator to hidden');
                    this.refreshIndicator.style.display = 'none';
                }
                
                // Show error message
                this.formError.textContent = data.message || 'Failed to save endpoint. Please try again.';
                this.formError.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Error saving endpoint:', error);
            
            // Hide loading state on refresh button
            if (this.refreshIndicator) {
                console.log('Setting refresh indicator to hidden in error handler');
                this.refreshIndicator.style.display = 'none';
            } else {
                console.error('Refresh indicator not found in error handler');
            }
            
            this.formError.textContent = 'Error saving endpoint: ' + error.message;
            this.formError.classList.remove('d-none');
        }
    }
    
    // Delete endpoint
    async deleteEndpoint() {
        try {
            const extension = this.confirmDeleteBtn.getAttribute('data-extension');
            
            // Show loading state on refresh button
            if (this.refreshIndicator) {
                console.log('Setting refresh indicator to visible');
                this.refreshIndicator.style.display = 'inline-block';
            } else {
                console.error('Refresh indicator not found');
            }
            
            // Send delete request
            const response = await fetch(`/api/endpoints/${extension}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Close modal
                this.deleteModal.hide();
                
                // Refresh endpoints by simulating a click on the refresh button
                console.log(`Refreshing dashboard after delete operation for endpoint ${extension}`);
                // Add a small delay to ensure AMI has time to process the changes
                setTimeout(() => {
                    console.log('Timeout completed, triggering refresh button click after delete');
                    if (this.refreshBtn) {
                        console.log('Clicking refresh button');
                        this.refreshBtn.click();
                    } else {
                        console.error('Refresh button not found');
                    }
                }, 500);
                
                // Show success message
                alert(`Endpoint ${extension} deleted successfully.`);
            } else {
                // Hide loading state on refresh button
                if (this.refreshIndicator) {
                    console.log('Setting refresh indicator to hidden');
                    this.refreshIndicator.style.display = 'none';
                }
                
                // Show error message
                alert(data.message || 'Failed to delete endpoint. Please try again.');
            }
        } catch (error) {
            console.error('Error deleting endpoint:', error);
            
            // Hide loading state on refresh button
            if (this.refreshIndicator) {
                console.log('Setting refresh indicator to hidden in error handler');
                this.refreshIndicator.style.display = 'none';
            } else {
                console.error('Refresh indicator not found in error handler');
            }
            
            alert('Error deleting endpoint: ' + error.message);
        }
    }
    
    // Validate form
    validateForm() {
        // Reset error message
        this.formError.classList.add('d-none');
        
        // Check if extension is valid
        const extension = this.endpointId.value.trim();
        if (!extension) {
            this.formError.textContent = 'Extension is required.';
            this.formError.classList.remove('d-none');
            return false;
        }
        
        if (!/^\d+$/.test(extension)) {
            this.formError.textContent = 'Extension must contain only digits.';
            this.formError.classList.remove('d-none');
            return false;
        }
        
        // Check if name is valid
        const name = this.endpointName.value.trim();
        if (!name) {
            this.formError.textContent = 'Name is required.';
            this.formError.classList.remove('d-none');
            return false;
        }
        
        // Check if password is valid for new endpoints
        const password = this.endpointPassword.value.trim();
        if (this.endpointAction.value === 'create' && !password) {
            this.formError.textContent = 'Password is required for new endpoints.';
            this.formError.classList.remove('d-none');
            return false;
        }
        
        // Check if at least one codec is selected
        if (!this.codecG722.checked && !this.codecUlaw.checked && !this.codecAlaw.checked) {
            this.formError.textContent = 'At least one codec must be selected.';
            this.formError.classList.remove('d-none');
            return false;
        }
        
        return true;
    }
}
