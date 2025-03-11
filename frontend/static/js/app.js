document.addEventListener('DOMContentLoaded', () => {
    // Store active calls information
    const activeCalls = {};
    
    // Store call duration timers
    const durationTimers = {};
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
        
        let statusColor = '#dc3545'; // Default red (unavailable)
        let displayState = state;
        let stateIcon = '';
        
        if (state === 'NOT INUSE' || state === 'NOT IN USE') {
            statusColor = '#28a745'; // Green
            displayState = 'Not In Use';
            stateIcon = `<i class="bi bi-telephone-x me-1" style="color: ${statusColor}"></i>`;
        } else if (state === 'BUSY' || state.includes('IN USE')) {
            statusColor = '#ffc107'; // Yellow
            displayState = 'Busy';
            stateIcon = `<i class="bi bi-telephone-minus me-1" style="color: ${statusColor}"></i>`;
        } else if (state === 'UNAVAILABLE') {
            statusColor = '#dc3545'; // Red
            displayState = 'Unavailable';
            stateIcon = `<i class="bi bi-dash-circle me-1" style="color: ${statusColor}"></i>`;
        } else if (state === 'CALLING') {
            statusColor = '#ff9900'; // Orange
            displayState = 'Calling';
            stateIcon = `<i class="bi bi-telephone-outbound me-1" style="color: ${statusColor}"></i>`;
        } else if (state === 'RINGING') {
            statusColor = '#ffcc00'; // Amber
            displayState = 'Ringing';
            stateIcon = `<i class="bi bi-telephone-vibrate me-1" style="color: ${statusColor}"></i>`;
        } else if (state === 'CONNECTED') {
            statusColor = '#00cc66'; // Bright green
            displayState = 'Connected';
            stateIcon = `<i class="bi bi-headset me-1" style="color: ${statusColor}"></i>`;
        }
        
        return `${stateIcon}<span style="color: ${statusColor}">${displayState}</span>`;
    }
    
    // Format timestamp
    function formatTimestamp(timestamp) {
        return new Date().toLocaleTimeString();
    }
    
    // Format duration in seconds to mm:ss format
    function formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
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
            
            // Format state with call direction and duration if available
            let stateHtml = formatState(endpoint.State);
            if (endpoint.callDirection) {
                stateHtml += `<span class="call-direction"><i class="bi bi-arrow-left-right"></i> ${endpoint.callDirection}</span>`;
            }
            if (endpoint.State === 'CONNECTED' && endpoint.callDuration) {
                stateHtml += `<span class="call-duration"><i class="bi bi-stopwatch"></i> ${endpoint.callDuration}</span>`;
            }
            
            row.innerHTML = `
                <td>${endpoint.Extension}</td>
                <td>${endpoint.Name}</td>
                <td>${stateHtml}</td>
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
    
    // Start a timer to update call duration
    function startDurationTimer(callId, extension1, extension2) {
        // Start time is when the call was answered
        const startTime = new Date(activeCalls[callId].answerTime || new Date());
        let durationSeconds = 0;
        
        // Update both extensions with the duration
        function updateDuration() {
            durationSeconds++;
            const durationText = formatDuration(durationSeconds);
            
            // Update UI with current duration for both extensions
            if (extension1) {
                updateCallDuration('PJSIP/' + extension1, `<i class="bi bi-arrow-left-right" style="color: #00cc66"></i> ${extension2}`, durationText);
            }
            
            if (extension2) {
                updateCallDuration('PJSIP/' + extension2, `<i class="bi bi-arrow-left-right" style="color: #00cc66"></i> ${extension1}`, durationText);
            }
        }
        
        // Start the timer and store it
        durationTimers[callId] = setInterval(updateDuration, 1000);
        
        // Initial call to display 00:00 immediately
        updateDuration();
    }
    
    // Update just the call duration without changing state
    function updateCallDuration(deviceName, callDirection, duration) {
        const extension = deviceName.split('/')[1];
        if (!extension) return;
        
        const endpoint = endpoints.find(ep => ep.Extension === extension);
        if (!endpoint) return;
        
        // Update the stored duration
        endpoint.callDuration = duration;
        
        // Update the UI
        const row = document.querySelector(`tr[data-extension="${extension}"]`);
        if (row) {
            const stateCell = row.cells[2];
            
            // Format state with call direction and duration
            let stateHtml = formatState('CONNECTED');
            if (callDirection) {
                stateHtml += `<span class="call-direction"><i class="bi bi-arrow-left-right"></i> ${callDirection}</span>`;
            }
            if (duration) {
                stateHtml += `<span class="call-duration"><i class="bi bi-stopwatch"></i> ${duration}</span>`;
            }
            
            stateCell.innerHTML = stateHtml;
        }
    }
    
    // Update endpoint state
    function updateEndpointState(deviceName, newState, callDirection) {
        // Extract extension from device name (format: PJSIP/XXX)
        const extension = deviceName.split('/')[1];
        if (!extension) return;
        
        // Find the endpoint in our data
        const endpoint = endpoints.find(ep => ep.Extension === extension);
        
        if (endpoint) {
            endpoint.State = newState;
            endpoint.callDirection = callDirection || '';
            endpoint.lastUpdated = formatTimestamp();
            
            // Update the specific table row
            const row = document.querySelector(`tr[data-extension="${extension}"]`);
            if (row) {
                const stateCell = row.cells[2];
                const timestampCell = row.cells[3];
                
                // Format state with call direction if available
                let stateHtml = formatState(newState);
                if (callDirection) {
                    stateHtml += `<span class="call-direction"><i class="bi bi-arrow-left-right"></i> ${callDirection}</span>`;
                }
                if (newState === 'CONNECTED' && endpoint.callDuration) {
                    stateHtml += `<span class="call-duration">${endpoint.callDuration}</span>`;
                }
                
                stateCell.innerHTML = stateHtml;
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
    
    // Process all events to update extension states
    function processEvent(eventData) {
        const eventType = eventData.Event;
        
        // Handle device state change events that come in different format
        if (!eventType && eventData.Device) {
            const extension = eventData.Device.split('/')[1];
            if (extension) {
                updateEndpointState('PJSIP/' + extension, eventData.State);
            }
            return;
        }
        
        // Skip if no event type
        if (!eventType) {
            console.log('No event type in data:', eventData);
            return;
        }
        
        // Extract channel information
        let extension, state, callInfo;
        
        switch(eventType) {
            case 'Newchannel':
                // When a new channel is created (outgoing call initiated)
                extension = eventData.CallerIDNum;
                state = 'CALLING';
                
                // Store the call destination if available
                if (eventData.Exten) {
                    const callerId = eventData.CallerIDNum;
                    const callDest = eventData.Exten;
                    
                    // Store call information
                    activeCalls[eventData.Uniqueid] = {
                        caller: callerId,
                        destination: callDest,
                        callerId: eventData.CallerIDNum,
                        callerName: eventData.CallerIDName,
                        status: 'calling',
                        startTime: new Date().toISOString(),
                        linkedId: eventData.Linkedid
                    };
                    
                    // Update with call direction information
                    callInfo = `→ ${callDest}`;
                }
                break;
                
            case 'DialState':
                // When a call is ringing
                if (eventData.DialStatus === 'RINGING') {
                    const callerId = eventData.CallerIDNum;
                    const destExtension = eventData.DestCallerIDNum;
                    
                    // Store call data with more context
                    if (eventData.Uniqueid && !activeCalls[eventData.Uniqueid]) {
                        activeCalls[eventData.Uniqueid] = {
                            caller: callerId,
                            destination: destExtension,
                            callerId: eventData.CallerIDNum,
                            callerName: eventData.CallerIDName,
                            destId: eventData.DestCallerIDNum,
                            destName: eventData.DestCallerIDName,
                            status: 'ringing',
                            linkedId: eventData.Linkedid,
                            destUniqueid: eventData.DestUniqueid
                        };
                    }
                    
                    // The originating extension is calling
                    if (callerId) {
                        updateEndpointState('PJSIP/' + callerId, 'CALLING', `<i class="bi bi-arrow-right" style="color: #ff9900"></i> ${destExtension}`);
                    }
                    
                    // The destination extension is ringing
                    if (destExtension) {
                        updateEndpointState('PJSIP/' + destExtension, 'RINGING', `<i class="bi bi-arrow-left" style="color: #ffcc00"></i> ${callerId}`);
                    }
                }
                return; // We've handled updates manually
                
            case 'DialEnd':
                // When a call is answered/connected
                if (eventData.DialStatus === 'ANSWER') {
                    const callerId = eventData.CallerIDNum;
                    const destExtension = eventData.DestCallerIDNum;
                    
                    // Update call status
                    if (eventData.Uniqueid && activeCalls[eventData.Uniqueid]) {
                        const callId = eventData.Uniqueid;
                        activeCalls[callId].status = 'connected';
                        activeCalls[callId].answerTime = new Date().toISOString();
                        
                        // Start duration timer for this call
                        startDurationTimer(callId, callerId, destExtension);
                    }
                    
                    // Both extensions are now connected
                    if (callerId) {
                        updateEndpointState('PJSIP/' + callerId, 'CONNECTED', `<i class="bi bi-arrow-left-right" style="color: #00cc66"></i> ${destExtension}`);
                    }
                    
                    if (destExtension) {
                        updateEndpointState('PJSIP/' + destExtension, 'CONNECTED', `<i class="bi bi-arrow-left-right" style="color: #00cc66"></i> ${callerId}`);
                    }
                }
                return; // We've handled updates manually
                
            case 'Hangup':
                // When a call is terminated
                extension = eventData.CallerIDNum;
                state = 'NOT INUSE';
                
                // Check if this extension was in a call
                const linkedId = eventData.Linkedid;
                if (linkedId) {
                    // Find all calls with this LinkedId
                    Object.keys(activeCalls).forEach(key => {
                        if (activeCalls[key].linkedId === linkedId) {
                            // Log who hung up
                            console.log(`Call ended: ${extension} hung up`);
                            
                            // If the call was connected, update both sides
                            if (activeCalls[key].status === 'connected') {
                                const otherParty = activeCalls[key].caller === extension ? 
                                    activeCalls[key].destination : activeCalls[key].caller;
                                    
                                if (otherParty) {
                                    updateEndpointState('PJSIP/' + otherParty, 'NOT INUSE');
                                }
                            }
                            
                            // Calculate call duration if it was connected
                            if (activeCalls[key].answerTime) {
                                const endTime = new Date();
                                const startTime = new Date(activeCalls[key].answerTime);
                                const duration = Math.round((endTime - startTime) / 1000);
                                console.log(`Call duration: ${duration} seconds`);
                            }
                            
                            // Stop the duration timer
                            if (durationTimers[key]) {
                                clearInterval(durationTimers[key]);
                                delete durationTimers[key];
                            }
                            
                            // Remove the call from active calls
                            delete activeCalls[key];
                        }
                    });
                }
                break;
                
            case 'DeviceStateChange':
                // Continue to handle standard device state changes
                extension = eventData.Device.split('/')[1];
                state = eventData.State;
                break;
                
            default:
                // For unhandled event types, log and return
                console.log('Unhandled event type:', eventType);
                return;
        }
        
        // Update device state if we have a valid extension
        if (extension) {
            updateEndpointState('PJSIP/' + extension, state, callInfo);
        }
    }
    
    // Initialize Socket.IO connection
    function initializeSocketConnection() {
        // Connect to the Socket.IO server
        connectionStatus.innerHTML = '<i class="bi bi-wifi"></i> Connecting...';
        connectionStatus.className = 'connection-status connection-disconnected';
        
        // We're assuming the Socket.IO server is at the same host as this page
        const socket = io();
        
        socket.on('connect', () => {
            console.log('Connected to Socket.IO server');
            connectionStatus.innerHTML = '<i class="bi bi-wifi"></i> Connected';
            connectionStatus.className = 'connection-status connection-connected';
        });
        
        socket.on('disconnect', () => {
            console.log('Disconnected from Socket.IO server');
            connectionStatus.innerHTML = '<i class="bi bi-wifi-off"></i> Disconnected';
            connectionStatus.className = 'connection-status connection-disconnected';
        });
        
        socket.on('EndpointStateChange', (data) => {
            console.log('EndpointStateChange event received:', data);
            if (data && data.data) {
                const eventData = data.data;
                console.log('Event data:', eventData);
                // Process all types of events
                processEvent(eventData);
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