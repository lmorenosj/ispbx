class CallMonitor {
    constructor() {
        this.activeCalls = {};
        this.durationTimers = {};
        this.callsTable = document.getElementById('calls-table');
        this.noCallsAlert = document.getElementById('no-calls');

        // Bind event handler methods
        this.handleEvent = this.handleEvent.bind(this);
    }

    // Format call status with icon and color
    formatCallStatus(status) {
        let statusColor = '#ffc107'; // Default yellow
        let statusIcon = '';
        
        switch(status) {
            case 'RINGING':
                statusColor = '#ffcc00';
                statusIcon = 'telephone-vibrate';
                break;
            case 'CONNECTED':
                statusColor = '#00cc66';
                statusIcon = 'headset';
                break;
            case 'CALLING':
                statusColor = '#ff9900';
                statusIcon = 'telephone-outbound';
                break;
        }
        
        return `<i class="bi bi-${statusIcon} me-1" style="color: ${statusColor}"></i><span style="color: ${statusColor}">${status}</span>`;
    }

    // Start a timer to update call duration
    startDurationTimer(callId) {
        const call = this.activeCalls[callId];
        if (!call) return;
        
        // Clear any existing timer
        if (this.durationTimers[callId]) {
            clearInterval(this.durationTimers[callId]);
        }
        
        // Start time is when the call was answered
        const startTime = call.answerTime || call.startTime;
        let durationSeconds = Math.floor((new Date() - startTime) / 1000);
        
        // Update duration
        const updateDuration = () => {
            durationSeconds++;
            call.duration = formatDuration(durationSeconds);
            this.renderCallsTable();
        };
        
        // Start the timer and store it
        this.durationTimers[callId] = setInterval(updateDuration, 1000);
        
        // Initial update
        updateDuration();
    }

    // Render active calls table
    renderCallsTable() {
        const activeCallsList = Object.values(this.activeCalls);
        this.callsTable.innerHTML = '';
        
        if (activeCallsList.length === 0) {
            this.noCallsAlert.classList.remove('d-none');
            return;
        }
        
        this.noCallsAlert.classList.add('d-none');
        
        activeCallsList.forEach(call => {
            const row = document.createElement('tr');
            row.setAttribute('data-call-id', call.id);
            
            // Calculate duration for calls not yet connected
            let duration = '00:00';
            if (call.status === 'CONNECTED' && call.answerTime) {
                duration = call.duration || formatDuration(Math.floor((new Date() - call.answerTime) / 1000));
            }
            
            row.innerHTML = `
                <td>${call.from}</td>
                <td>${call.to || '-'}</td>
                <td>${this.formatCallStatus(call.status)}</td>
                <td>${duration}</td>
                <td>${new Date(call.startTime).toLocaleTimeString()}</td>
            `;
            
            this.callsTable.appendChild(row);
        });
    }

    // Handle call events
    handleEvent(eventData) {
        // Extract event data from wrapper if needed
        const data = eventData.data || eventData;
        const event = data.Event;
        
        switch (event) {
            case 'Newchannel':
                // Only create call entry for the originating channel
                if (data.CallerIDNum !== '<unknown>' && data.Exten) {
                    const callId = data.Linkedid;
                    
                    // Store call information
                    this.activeCalls[callId] = {
                        id: callId,
                        from: data.CallerIDNum,
                        to: data.Exten,
                        startTime: new Date(),
                        status: 'CALLING',
                        channels: new Set([data.Uniqueid])
                    };
                    
                    this.renderCallsTable();
                }
                break;
                
            case 'DialState':
                const dialCallId = data.Linkedid;
                if (this.activeCalls[dialCallId]) {
                    const call = this.activeCalls[dialCallId];
                    
                    // Update call status
                    call.status = data.DialStatus;
                    
                    // Add both channels
                    call.channels.add(data.Uniqueid);
                    call.channels.add(data.DestUniqueid);
                    
                    // Update destination info
                    if (data.DestCallerIDNum && data.DestCallerIDNum !== '<unknown>') {
                        call.to = data.DestCallerIDNum;
                    }
                    
                    this.renderCallsTable();
                }
                break;
                
            case 'DialEnd':
                const endCallId = data.Linkedid;
                if (this.activeCalls[endCallId] && data.DialStatus === 'ANSWER') {
                    const call = this.activeCalls[endCallId];
                    call.status = 'CONNECTED';
                    call.answerTime = new Date();
                    
                    // Start duration timer
                    this.startDurationTimer(endCallId);
                    this.renderCallsTable();
                }
                break;
                
            case 'Hangup':
                // Find call by Linkedid
                const hangupCallId = data.Linkedid;
                if (this.activeCalls[hangupCallId]) {
                    const call = this.activeCalls[hangupCallId];
                    
                    // Remove the hung up channel
                    call.channels.delete(data.Uniqueid);
                    
                    // If all channels are gone, end the call
                    if (call.channels.size === 0) {
                        // Clear duration timer
                        if (this.durationTimers[hangupCallId]) {
                            clearInterval(this.durationTimers[hangupCallId]);
                            delete this.durationTimers[hangupCallId];
                        }
                        
                        // Remove call from active calls
                        delete this.activeCalls[hangupCallId];
                    }
                    
                    this.renderCallsTable();
                }
                break;
        }
    }

    // Initialize the monitor
    initialize() {
        // Initial render of empty table
        this.renderCallsTable();
    }
}
