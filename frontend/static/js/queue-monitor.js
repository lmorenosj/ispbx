class QueueMonitor {
    constructor() {
        // References to DOM elements
        this.queuesTable = document.getElementById('queues-table');
        this.queueDetailsContainer = document.getElementById('queue-details');
        this.queueMembersTable = document.getElementById('queue-members-table');
        this.queueLoadingIndicator = document.getElementById('queue-loading-indicator');
        this.queueNoData = document.getElementById('queue-no-data');
        this.queueDetailsLoadingIndicator = document.getElementById('queue-details-loading-indicator');
        this.queueDetailsNoData = document.getElementById('queue-details-no-data');
        
        // Current queue being viewed
        this.currentQueueName = null;
        
        // Refresh interval
        this.refreshInterval = null;
        this.refreshRate = 10000; // 10 seconds
    }
    
    // Initialize the queue monitor
    initialize() {
        console.info('Initializing QueueMonitor');
        
        // Initial data load
        this.refreshQueues();
        
/*         // Set up refresh interval
        this.refreshInterval = setInterval(() => {
            this.refreshQueues();
            if (this.currentQueueName) {
                this.refreshQueueDetails(this.currentQueueName);
            }
        }, this.refreshRate); */
        
        // Add event listeners for queue selection
        document.addEventListener('click', (event) => {
            // View queue details button
            const viewButton = event.target.matches('.view-queue-btn') ? 
                event.target : event.target.closest('.view-queue-btn');
                
            if (viewButton) {
                const queueName = viewButton.getAttribute('data-queue');
                this.showQueueDetails(queueName);
                return;
            }
            
            // Back to list button
            if (event.target.matches('#backToQueuesBtn') || event.target.closest('#backToQueuesBtn')) {
                this.hideQueueDetails();
                return;
            }
        });
    }
    
    // Clean up resources
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    // Refresh the list of queues
    async refreshQueues() {
        try {
            // If queue details are currently shown, don't refresh the list
            if (this.queueDetailsContainer && !this.queueDetailsContainer.classList.contains('d-none')) {
                return;
            }
            
            // Show loading indicator if table is empty
            if (!this.queuesTable.querySelector('tr')) {
                this.queueLoadingIndicator.classList.remove('d-none');
                this.queueNoData.classList.add('d-none');
            }
            
            // Fetch queues from API
            const { status, data } = await fetchAPI(API_CONFIG.QUEUES.DB_LIST);
            console.log(`Queue response status: ${status}`);
            console.log('Queue response data:', data);
            // Hide loading indicator
            this.queueLoadingIndicator.classList.add('d-none');
            
            if (data.status === 'success' && data.queues && data.queues.length > 0) {
                // Clear existing table
                this.queuesTable.innerHTML = '';
                console.debug('[QueueMonitor] Adding queues to table:', data.queues);
                // Add queues to table
                data.queues.forEach(queue => {
                    this.addQueueToTable(queue);
                });
                
                // Hide no data message
                this.queueNoData.classList.add('d-none');
            } else {
                // Show no data message
                this.queueNoData.classList.remove('d-none');
                this.queuesTable.innerHTML = '';
            }
        } catch (error) {
            console.error('Error refreshing queues:', error);
            this.queueLoadingIndicator.classList.add('d-none');
            this.queueNoData.classList.remove('d-none');
            this.queueNoData.textContent = `Error loading queues: ${error.message}`;
        }
    }
    
    // Add a queue to the table
    addQueueToTable(queue) {
        const row = document.createElement('tr');
        
        // Format the queue data
        const queueName = queue.name;
        const strategy = queue.strategy || 'ringall';
        const memberCount = queue.member_count || 0;
        
        // Create table cells
        row.innerHTML = `
            <td>${queueName}</td>
            <td>${strategy}</td>
            <td>${memberCount}</td>
            <td class="text-end">
                <button class="btn btn-sm btn-info view-queue-btn" data-queue="${queueName}">
                    <i class="bi bi-eye"></i> View
                </button>
                <button class="btn btn-sm btn-primary edit-queue-btn" data-queue="${queueName}">
                    <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn btn-sm btn-danger delete-queue-btn" data-queue="${queueName}">
                    <i class="bi bi-trash"></i> Delete
                </button>
            </td>
        `;
        
        // Add row to table
        this.queuesTable.appendChild(row);
    }
    
    async showQueueDetails(queueName) {
        try {
            console.debug('Showing queue details:', queueName);
            // Store current queue name
            this.currentQueueName = queueName;
            
            // Update queue name in header
            document.getElementById('queue-name').textContent = queueName;
            
            // Update the "Add Member" button with the current queue name
            const addMemberBtn = document.querySelector('.add-member-btn');
            if (addMemberBtn) {
                addMemberBtn.setAttribute('data-queue', queueName);
            }
            
            // Hide queues list and show details
            document.getElementById('queues-list-container').classList.add('d-none');
            this.queueDetailsContainer.classList.remove('d-none');
            
            // Refresh queue details
            await this.refreshQueueDetails(queueName);
        } catch (error) {
            console.error('Error showing queue details:', error);
        }
    }
    
    // Hide queue details and show list
    hideQueueDetails() {
        // Clear current queue
        this.currentQueueName = null;
        
        // Hide details and show list
        this.queueDetailsContainer.classList.add('d-none');
        document.getElementById('queues-list-container').classList.remove('d-none');
        
        // Refresh queues list
        this.refreshQueues();
    }
    
    // Refresh queue details
    async refreshQueueDetails(queueName) {
        try {
            // Show loading indicator
            this.queueDetailsLoadingIndicator.classList.remove('d-none');
            this.queueDetailsNoData.classList.add('d-none');
            
            // Fetch queue details from API
            const { status, data } = await fetchAPI(API_CONFIG.QUEUES.DB_GET(queueName));
            
            // Hide loading indicator
            this.queueDetailsLoadingIndicator.classList.add('d-none');
            
            if (data.status === 'success' && data.queue) {
                // Update queue details
                this.updateQueueDetails(data.queue);
                
                // Fetch queue members
                await this.refreshQueueMembers(queueName);
                
                // Hide no data message
                this.queueDetailsNoData.classList.add('d-none');
            } else {
                // Show no data message
                this.queueDetailsNoData.classList.remove('d-none');
                this.queueMembersTable.innerHTML = '';
            }
        } catch (error) {
            console.error('Error refreshing queue details:', error);
            this.queueDetailsLoadingIndicator.classList.add('d-none');
            this.queueDetailsNoData.classList.remove('d-none');
            this.queueDetailsNoData.textContent = `Error loading queue details: ${error.message}`;
        }
    }
    
    // Update queue details in UI
    updateQueueDetails(queueData) {
        const queue = queueData.queue;
        
        // Update basic information
        document.getElementById('queue-strategy').textContent = queue.strategy ?? 'ringall';
        document.getElementById('queue-timeout').textContent = queue.timeout ?? '-';
        document.getElementById('queue-musiconhold').textContent = queue.musiconhold ?? 'default';
        document.getElementById('queue-announce').textContent = queue.announce ?? '-';
        document.getElementById('queue-context').textContent = queue.context ?? 'from-queue';
        document.getElementById('queue-maxlen').textContent = queue.maxlen ?? '0';
        document.getElementById('queue-servicelevel').textContent = queue.servicelevel ?? '60';
        document.getElementById('queue-wrapuptime').textContent = queue.wrapuptime ?? '0';
/*         // Update status information if available
        if (queueData.status) {
            document.getElementById('queue-calls').textContent = queueData.status.calls ?? '0';
            document.getElementById('queue-completed').textContent = queueData.status.completed ?? '0';
            document.getElementById('queue-abandoned').textContent = queueData.status.abandoned ?? '0'; 
            document.getElementById('queue-holdtime').textContent = queueData.status.holdtime ? formatSeconds(queueData.status.holdtime) : '0s';
            document.getElementById('queue-talktime').textContent = queueData.status.talktime ? formatSeconds(queueData.status.talktime) : '0s';
        } else {
            // Reset status fields if no status data
            document.getElementById('queue-calls').textContent = '0';
            document.getElementById('queue-completed').textContent = '0';
            document.getElementById('queue-abandoned').textContent = '0';
            document.getElementById('queue-holdtime').textContent = '0s';
            document.getElementById('queue-talktime').textContent = '0s';
        } */
    }
    
    // Refresh queue members
    async refreshQueueMembers(queueName) {
        try {
            // Fetch queue members from API
            const {status, data} = await fetchAPI(API_CONFIG.QUEUE_MEMBERS.LIST(queueName));
            
            console.debug('Queue members:', data);
            // Clear existing members table
            this.queueMembersTable.innerHTML = '';
            
            if (data.status === 'success' && data.members) {
                // Add members to table
                if(data.members.length > 0) {
                    data.members.forEach(member => {
                        this.addMemberToTable(queueName, member);
                    });
                }
                
                // Show members table
                document.getElementById('queue-members-container').classList.remove('d-none');
            } else {
                // Hide members table if no members
                document.getElementById('queue-members-container').classList.add('d-none');
            }
        } catch (error) {
            console.error('Error refreshing queue members:', error);
            document.getElementById('queue-members-container').classList.add('d-none');
        }
    }
    
    // Add a member to the table
    addMemberToTable(queueName, member) {
        const row = document.createElement('tr');
        
        // Format the member data
        const interfaceName = member.interface || '';
        const name = member.membername || interfaceName.split('/').pop() || '';
        const penalty = member.penalty || '0';
        const paused = member.paused ? 'Yes' : 'No';
        const status = member.status || 'Unknown';
        
        // Create table cells
        row.innerHTML = `
            <td>${interfaceName}</td>
            <td>${name}</td>
            <td>${penalty}</td>
            <td>${paused}</td>
            <td>${status}</td>
            <td class="text-end">
                <button class="btn btn-sm btn-danger remove-member-btn" data-queue="${queueName}" data-interface="${interfaceName}">
                    <i class="bi bi-trash"></i> Remove
                </button>
            </td>
        `;
        
        // Add row to table
        this.queueMembersTable.appendChild(row);
    }
}

// Helper function to format seconds into a readable time string
function formatSeconds(seconds) {
    if (!seconds || isNaN(seconds)) return '0s';
    
    seconds = parseInt(seconds);
    
    if (seconds < 60) {
        return `${seconds}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const remainingMinutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;
        return `${hours}h ${remainingMinutes}m ${remainingSeconds}s`;
    }
}

// Initialize the queue monitor when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.queueMonitor = new QueueMonitor();
    window.queueMonitor.initialize();
});
