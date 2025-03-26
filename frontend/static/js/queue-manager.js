class QueueManager {
    constructor() {
        // Modal elements
        this.queueModal = new bootstrap.Modal(document.getElementById('queueModal'));
        this.deleteModal = new bootstrap.Modal(document.getElementById('deleteQueueModal'));
        this.memberModal = new bootstrap.Modal(document.getElementById('queueMemberModal'));
        
        // Form elements
        this.queueForm = document.getElementById('queueForm');
        this.queueAction = document.getElementById('queueAction');
        this.queueName = document.getElementById('queueName');
        this.queueStrategy = document.getElementById('queueStrategy');
        this.queueTimeout = document.getElementById('queueTimeout');
        this.queueMusicOnHold = document.getElementById('queueMusicOnHold');
        this.queueAnnounce = document.getElementById('queueAnnounce');
        this.queueContext = document.getElementById('queueContext');
        this.queueMaxlen = document.getElementById('queueMaxlen');
        this.queueServicelevel = document.getElementById('queueServicelevel');
        this.queueWrapuptime = document.getElementById('queueWrapuptime');
        this.formError = document.getElementById('queueFormError');
        
        // Member form elements
        this.memberForm = document.getElementById('queueMemberForm');
        this.memberQueueName = document.getElementById('memberQueueName');
        this.memberInterface = document.getElementById('memberInterface');
        this.memberName = document.getElementById('memberName');
        this.memberPenalty = document.getElementById('memberPenalty');
        this.memberPaused = document.getElementById('memberPaused');
        this.memberWrapuptime = document.getElementById('memberWrapuptime');
        this.memberFormError = document.getElementById('queueMemberFormError');
        
        // Buttons
        this.saveQueueBtn = document.getElementById('saveQueueBtn');
        this.confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        this.deleteQueueName = document.getElementById('deleteQueueName');
        this.saveMemberBtn = document.getElementById('saveMemberBtn');
        
        // Reference to the refresh button and indicator
        this.refreshBtn = document.getElementById('refresh-btn');
        this.refreshIndicator = document.getElementById('refresh-indicator');
        
        // Bind event handlers
        this.saveQueueBtn.addEventListener('click', () => this.saveQueue());
        this.confirmDeleteBtn.addEventListener('click', () => this.deleteQueue());
        this.saveMemberBtn.addEventListener('click', () => this.saveQueueMember());
    }
    
    // Initialize the queue manager
    initialize() {
        console.info('Initializing QueueManager');
        
        // Add event listeners for the add, edit, and delete buttons
        document.addEventListener('click', (event) => {
            console.debug('Click event detected:', event.target);
            
            // Add queue button
            if (event.target.matches('#addQueueBtn') || event.target.closest('#addQueueBtn')) {
                this.showAddQueueModal();
                return;
            }
            
            // Edit queue button - handle both the button and the icon inside it
            const editButton = event.target.matches('.edit-queue-btn') ? 
                event.target : event.target.closest('.edit-queue-btn');
                
            if (editButton) {
                const queueName = editButton.getAttribute('data-queue');
                this.showEditQueueModal(queueName);
                return;
            }
            
            // Delete queue button - handle both the button and the icon inside it
            const deleteButton = event.target.matches('.delete-queue-btn') ? 
                event.target : event.target.closest('.delete-queue-btn');
                
            if (deleteButton) {
                const queueName = deleteButton.getAttribute('data-queue');
                this.showDeleteQueueModal(queueName);
                return;
            }
            
            // Add member button
            if (event.target.matches('.add-member-btn') || event.target.closest('.add-member-btn')) {
                const queueName = event.target.getAttribute('data-queue') || 
                                 event.target.closest('.add-member-btn').getAttribute('data-queue');
                this.showAddMemberModal(queueName);
                return;
            }
            
            // Remove member button
            const removeMemberButton = event.target.matches('.remove-member-btn') ? 
                event.target : event.target.closest('.remove-member-btn');
                
            if (removeMemberButton) {
                const queueName = removeMemberButton.getAttribute('data-queue');
                const interfaceName = removeMemberButton.getAttribute('data-interface');
                this.removeQueueMember(queueName, interfaceName);
                return;
            }
        });
    }
    
    // Show modal for adding a new queue
    showAddQueueModal() {
        // Reset form
        this.queueForm.reset();
        this.formError.classList.add('d-none');
        
        // Set action to create
        this.queueAction.value = 'create';
        
        // Enable queue name field
        this.queueName.disabled = false;
        
        // Set default values
        this.queueStrategy.value = 'ringall';
        this.queueTimeout.value = '15';
        this.queueMusicOnHold.value = 'default';
        this.queueContext.value = 'from-queue';
        this.queueMaxlen.value = '0';
        this.queueServicelevel.value = '60';
        this.queueWrapuptime.value = '0';
        
        // Update modal title
        document.getElementById('queueModalLabel').textContent = 'Add New Queue';
        
        // Show modal
        this.queueModal.show();
    }
    
    // Show modal for editing an existing queue
    async showEditQueueModal(queueName) {
        try {            
            // Reset form and show loading state
            this.queueForm.reset();
            this.formError.classList.add('d-none');
            
            // Set action to update
            this.queueAction.value = 'update';
            
            // Update modal title
            document.getElementById('queueModalLabel').textContent = 'Edit Queue';
            
            // Pre-fill the queue name and disable it
            this.queueName.value = queueName;
            this.queueName.disabled = true; // Can't change the queue name
            
            // Show the modal immediately to provide feedback to the user
            this.queueModal.show();
            
            // Fetch queue details directly from backend
            try {
                const response = await fetch(`/api/queues/${queueName}`);
                const data = await response.json();
                console.debug('[FetchAPI] Queue data received:', data);
                
                if (data.status === 'success' && data.queue) {
                    const queue = data.queue.queue;
                    
                    // Set form values
                    this.queueStrategy.value = queue.strategy || 'ringall';
                    this.queueTimeout.value = queue.timeout || '15';
                    this.queueMusicOnHold.value = queue.musiconhold || 'default';
                    this.queueAnnounce.value = queue.announce || '';
                    this.queueContext.value = queue.context || 'from-queue';
                    this.queueMaxlen.value = queue.maxlen || '0';
                    this.queueServicelevel.value = queue.servicelevel || '60';
                    this.queueWrapuptime.value = queue.wrapuptime || '0';
                } else {
                    console.error('Failed to fetch queue details:', data);
                    this.formError.textContent = 'Failed to load queue details. Please try again.';
                    this.formError.classList.remove('d-none');
                }
            } catch (apiError) {
                console.error('[FetchAPI] API error fetching queue details:', apiError);
                this.formError.textContent = 'Error loading queue details: ' + apiError.message;
                this.formError.classList.remove('d-none');
            }
        } catch (error) {
            this.formError.textContent = 'Error loading queue details: ' + error.message;
            this.formError.classList.remove('d-none');
        }
    }
    
    // Show confirmation modal for deleting a queue
    showDeleteQueueModal(queueName) {
        this.deleteQueueName.textContent = queueName;
        this.confirmDeleteBtn.setAttribute('data-queue', queueName);
        this.deleteModal.show();
    }
    
    // Show modal for adding a member to a queue
    showAddMemberModal(queueName) {
        // Reset form
        this.memberForm.reset();
        this.memberFormError.classList.add('d-none');
        
        // Set queue name
        this.memberQueueName.value = queueName;
        this.memberQueueName.disabled = true;
        
        // Set default values
        this.memberPenalty.value = '0';
        this.memberPaused.checked = false;
        this.memberWrapuptime.value = '';
        
        // Update modal title
        document.getElementById('queueMemberModalLabel').textContent = `Add Member to Queue: ${queueName}`;
        
        // Fetch available endpoints for the dropdown
        this.loadAvailableEndpoints();
        
        // Show modal
        this.memberModal.show();
    }
    
    // Load available endpoints for the member dropdown
    async loadAvailableEndpoints() {
        try {
            const response = await fetch('/api/endpoints/db');
            const data = await response.json();
            
            if (data.status === 'success' && data.endpoints) {
                const select = this.memberInterface;
                
                // Clear existing options
                select.innerHTML = '';
                
                // Add default option
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Select an endpoint';
                defaultOption.selected = true;
                defaultOption.disabled = true;
                select.appendChild(defaultOption);
                
                // Add endpoints as options
                data.endpoints.forEach(endpoint => {
                    const option = document.createElement('option');
                    option.value = `PJSIP/${endpoint.id}`;
                    
                    // Extract name from callerid if available
                    let displayName = endpoint.id;
                    if (endpoint.callerid) {
                        const nameMatch = endpoint.callerid.match(/"([^"]+)"/);
                        if (nameMatch) {
                            displayName = `${nameMatch[1]} (${endpoint.id})`;
                        }
                    }
                    
                    option.textContent = displayName;
                    select.appendChild(option);
                });
            } else {
                console.error('Failed to fetch endpoints:', data);
                this.memberFormError.textContent = 'Failed to load available endpoints. Please try again.';
                this.memberFormError.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Error fetching endpoints:', error);
            this.memberFormError.textContent = 'Error loading available endpoints: ' + error.message;
            this.memberFormError.classList.remove('d-none');
        }
    }
    
    // Validate queue form
    validateQueueForm() {
        // Reset error message
        this.formError.classList.add('d-none');
        
        // Check required fields
        if (!this.queueName.value.trim()) {
            this.formError.textContent = 'Queue name is required';
            this.formError.classList.remove('d-none');
            return false;
        }
        
        // Validate queue name format (alphanumeric and hyphens only)
        const queueNameRegex = /^[a-zA-Z0-9-_]+$/;
        if (!queueNameRegex.test(this.queueName.value.trim())) {
            this.formError.textContent = 'Queue name can only contain letters, numbers, hyphens, and underscores';
            this.formError.classList.remove('d-none');
            return false;
        }
        
        // Validate numeric fields
        const numericFields = [
            { field: this.queueTimeout, name: 'Timeout', min: 0 },
            { field: this.queueMaxlen, name: 'Max Length', min: 0 },
            { field: this.queueServicelevel, name: 'Service Level', min: 0 },
            { field: this.queueWrapuptime, name: 'Wrapup Time', min: 0 }
        ];
        
        for (const { field, name, min } of numericFields) {
            if (field.value.trim() !== '') {
                const value = parseInt(field.value.trim());
                if (isNaN(value) || value < min) {
                    this.formError.textContent = `${name} must be a number greater than or equal to ${min}`;
                    this.formError.classList.remove('d-none');
                    return false;
                }
            }
        }
        
        return true;
    }
    
    // Validate member form
    validateMemberForm() {
        // Reset error message
        this.memberFormError.classList.add('d-none');
        
        // Check required fields
        if (!this.memberQueueName.value.trim()) {
            this.memberFormError.textContent = 'Queue name is required';
            this.memberFormError.classList.remove('d-none');
            return false;
        }
        
        if (!this.memberInterface.value.trim()) {
            this.memberFormError.textContent = 'Please select an endpoint';
            this.memberFormError.classList.remove('d-none');
            return false;
        }
        
        // Validate numeric fields
        const numericFields = [
            { field: this.memberPenalty, name: 'Penalty', min: 0 },
            { field: this.memberWrapuptime, name: 'Wrapup Time', min: 0 }
        ];
        
        for (const { field, name, min } of numericFields) {
            if (field.value.trim() !== '') {
                const value = parseInt(field.value.trim());
                if (isNaN(value) || value < min) {
                    this.memberFormError.textContent = `${name} must be a number greater than or equal to ${min}`;
                    this.memberFormError.classList.remove('d-none');
                    return false;
                }
            }
        }
        
        return true;
    }
    
    // Save queue (create or update)
    async saveQueue() {
        console.info('saveQueue method called');
        try {
            // Validate form
            if (!this.validateQueueForm()) {
                console.warn('Form validation failed');
                return;
            }
            console.debug('Form validation passed');
            
            // Get form values
            const queueName = this.queueName.value.trim();
            const strategy = this.queueStrategy.value.trim();
            const timeout = parseInt(this.queueTimeout.value.trim() || '15');
            const musiconhold = this.queueMusicOnHold.value.trim();
            const announce = this.queueAnnounce.value.trim() || null;
            const context = this.queueContext.value.trim();
            const maxlen = parseInt(this.queueMaxlen.value.trim() || '0');
            const servicelevel = parseInt(this.queueServicelevel.value.trim() || '60');
            const wrapuptime = parseInt(this.queueWrapuptime.value.trim() || '0');
            
            // Prepare request payload
            const payload = {
                queue_name: queueName,
                strategy,
                timeout,
                musiconhold,
                announce,
                context,
                maxlen,
                servicelevel,
                wrapuptime
            };
            
            // Determine if this is a create or update operation
            const isCreate = this.queueAction.value === 'create';
            
            // Set up the request
            const url = isCreate ? '/api/queues' : `/api/queues/${queueName}`;
            const method = isCreate ? 'POST' : 'PUT';
            
            // If updating, remove queue_name from payload
            if (!isCreate) {
                delete payload.queue_name;
            }
            
            // Show loading state
            this.saveQueueBtn.disabled = true;
            this.saveQueueBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            
            // Send the request
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            // Reset button state
            this.saveQueueBtn.disabled = false;
            this.saveQueueBtn.textContent = 'Save';
            
            if (response.ok) {
                console.info(`Queue ${isCreate ? 'created' : 'updated'} successfully:`, data);
                
                // Close the modal
                this.queueModal.hide();
                
                // Refresh the queues list
                if (window.queueMonitor) {
                    window.queueMonitor.refreshQueues();
                }
                
                // Show success message
                showToast(`Queue ${queueName} ${isCreate ? 'created' : 'updated'} successfully`);
            } else {
                console.error(`Failed to ${isCreate ? 'create' : 'update'} queue:`, data);
                this.formError.textContent = data.detail || `Failed to ${isCreate ? 'create' : 'update'} queue. Please try again.`;
                this.formError.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Error saving queue:', error);
            this.saveQueueBtn.disabled = false;
            this.saveQueueBtn.textContent = 'Save';
            this.formError.textContent = `Error: ${error.message}`;
            this.formError.classList.remove('d-none');
        }
    }
    
    // Delete queue
    async deleteQueue() {
        try {
            const queueName = this.confirmDeleteBtn.getAttribute('data-queue');
            
            // Show loading state
            this.confirmDeleteBtn.disabled = true;
            this.confirmDeleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Deleting...';
            
            // Send delete request
            const response = await fetch(`/api/queues/${queueName}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            // Reset button state
            this.confirmDeleteBtn.disabled = false;
            this.confirmDeleteBtn.textContent = 'Delete';
            
            if (response.ok) {
                console.info('Queue deleted successfully:', data);
                
                // Close the modal
                this.deleteModal.hide();
                
                // Refresh the queues list
                if (window.queueMonitor) {
                    window.queueMonitor.refreshQueues();
                }
                
                // Show success message
                showToast(`Queue ${queueName} deleted successfully`);
            } else {
                console.error('Failed to delete queue:', data);
                showToast(`Failed to delete queue: ${data.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting queue:', error);
            this.confirmDeleteBtn.disabled = false;
            this.confirmDeleteBtn.textContent = 'Delete';
            showToast(`Error deleting queue: ${error.message}`, 'error');
        }
    }
    
    // Save queue member
    async saveQueueMember() {
        console.info('saveQueueMember method called');
        try {
            // Validate form
            if (!this.validateMemberForm()) {
                console.warn('Form validation failed');
                return;
            }
            console.debug('Form validation passed');
            
            // Get form values
            const queueName = this.memberQueueName.value.trim();
            const interfaceName = this.memberInterface.value.trim();
            const membername = this.memberName.value.trim() || null;
            const penalty = parseInt(this.memberPenalty.value.trim() || '0');
            const paused = this.memberPaused.checked ? 1 : 0;
            const wrapuptime = this.memberWrapuptime.value.trim() ? parseInt(this.memberWrapuptime.value.trim()) : null;
            
            // Prepare request payload
            const payload = {
                interface: interfaceName,
                membername,
                penalty,
                paused,
                wrapuptime
            };
            
            // Show loading state
            this.saveMemberBtn.disabled = true;
            this.saveMemberBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            
            // Send the request
            const response = await fetch(`/api/queues/${queueName}/members`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            // Reset button state
            this.saveMemberBtn.disabled = false;
            this.saveMemberBtn.textContent = 'Add Member';
            
            if (response.ok) {
                console.info('Member added successfully:', data);
                
                // Close the modal
                this.memberModal.hide();
                
                // Refresh the queue details
                if (window.queueMonitor) {
                    window.queueMonitor.refreshQueueDetails(queueName);
                }
                
                // Show success message
                showToast(`Member added to queue ${queueName} successfully`);
            } else {
                console.error('Failed to add member:', data);
                this.memberFormError.textContent = data.detail || 'Failed to add member. Please try again.';
                this.memberFormError.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Error adding member:', error);
            this.saveMemberBtn.disabled = false;
            this.saveMemberBtn.textContent = 'Add Member';
            this.memberFormError.textContent = `Error: ${error.message}`;
            this.memberFormError.classList.remove('d-none');
        }
    }
    
    // Remove a member from a queue
    async removeQueueMember(queueName, interfaceName) {
        try {
            // Confirm with the user
            if (!confirm(`Are you sure you want to remove ${interfaceName} from queue ${queueName}?`)) {
                return;
            }
            
            // Send delete request
            const response = await fetch(`/api/queues/${queueName}/members/${encodeURIComponent(interfaceName)}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                console.info('Member removed successfully:', data);
                
                // Refresh the queue details
                if (window.queueMonitor) {
                    window.queueMonitor.refreshQueueDetails(queueName);
                }
                
                // Show success message
                showToast(`Member removed from queue ${queueName} successfully`);
            } else {
                console.error('Failed to remove member:', data);
                showToast(`Failed to remove member: ${data.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('Error removing member:', error);
            showToast(`Error removing member: ${error.message}`, 'error');
        }
    }
}

// Initialize the queue manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.queueManager = new QueueManager();
    window.queueManager.initialize();
});
