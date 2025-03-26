/**
 * CDR Manager - Handles fetching and displaying Call Detail Records
 */
class CDRManager {
    constructor() {
        this.records = [];
        this.stats = {};
        this.currentPage = 1;
        this.recordsPerPage = 25;
        this.totalRecords = 0;
        this.filters = {
            start_date: null,
            end_date: null,
            src: null,
            dst: null,
            disposition: null
        };
        
        // DOM elements
        this.filterForm = document.getElementById('cdr-filter-form');
        this.clearFiltersBtn = document.getElementById('clear-filters');
        this.exportCsvBtn = document.getElementById('export-csv');
        this.cdrTable = document.getElementById('cdr-table');
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.noRecordsMessage = document.getElementById('no-records');
        this.recordsShowing = document.getElementById('records-showing');
        this.recordsTotal = document.getElementById('records-total');
        this.pagination = document.getElementById('cdr-pagination');
        
        // Stats elements
        this.totalCallsElement = document.getElementById('total-calls');
        this.answeredCallsElement = document.getElementById('answered-calls');
        this.callsTodayElement = document.getElementById('calls-today');
        this.avgDurationElement = document.getElementById('avg-duration');
        
        // Initialize datepickers
        this.initDatepickers();
        
        // Bind event listeners
        this.bindEvents();
        
        // Initial data load
        this.fetchStats();
        this.fetchRecords();
    }
    
    /**
     * Initialize datepicker controls
     */
    initDatepickers() {
        flatpickr('#start-date', {
            dateFormat: 'Y-m-d',
            allowInput: true,
            onChange: (selectedDates, dateStr) => {
                this.filters.start_date = dateStr || null;
            }
        });
        
        flatpickr('#end-date', {
            dateFormat: 'Y-m-d',
            allowInput: true,
            onChange: (selectedDates, dateStr) => {
                this.filters.end_date = dateStr || null;
            }
        });
    }
    
    /**
     * Bind event listeners to DOM elements
     */
    bindEvents() {
        // Filter form submission
        this.filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateFiltersFromForm();
            this.currentPage = 1; // Reset to first page when applying new filters
            this.fetchRecords();
        });
        
        // Clear filters button
        this.clearFiltersBtn.addEventListener('click', () => {
            this.clearFilters();
        });
        
        // Export to CSV button
        this.exportCsvBtn.addEventListener('click', () => {
            this.exportToCSV();
        });
        
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.fetchStats();
            this.fetchRecords();
        });
    }
    
    /**
     * Update filter values from form inputs
     */
    updateFiltersFromForm() {
        this.filters.src = document.getElementById('src').value || null;
        this.filters.dst = document.getElementById('dst').value || null;
        this.filters.disposition = document.getElementById('disposition').value || null;
        // start_date and end_date are updated by the datepicker onChange events
    }
    
    /**
     * Clear all filters and reset form
     */
    clearFilters() {
        // Reset form fields
        document.getElementById('start-date').value = '';
        document.getElementById('end-date').value = '';
        document.getElementById('src').value = '';
        document.getElementById('dst').value = '';
        document.getElementById('disposition').value = '';
        
        // Reset filter values
        this.filters = {
            start_date: null,
            end_date: null,
            src: null,
            dst: null,
            disposition: null
        };
        
        // Reset datepickers
        const startDatePicker = document.getElementById('start-date')._flatpickr;
        const endDatePicker = document.getElementById('end-date')._flatpickr;
        if (startDatePicker) startDatePicker.clear();
        if (endDatePicker) endDatePicker.clear();
        
        // Fetch records with cleared filters
        this.currentPage = 1;
        this.fetchRecords();
    }
    
    /**
     * Fetch CDR statistics from API
     */
    async fetchStats() {
        try {
            const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/cdr/stats`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.stats = data.stats;
                this.updateStatsDisplay();
            } else {
                console.error('Error fetching CDR stats:', data);
            }
        } catch (error) {
            console.error('Error fetching CDR stats:', error);
        }
    }
    
    /**
     * Update the statistics display with current data
     */
    updateStatsDisplay() {
        this.totalCallsElement.textContent = this.stats.total_calls || 0;
        this.answeredCallsElement.textContent = this.stats.disposition_stats?.ANSWERED || 0;
        this.callsTodayElement.textContent = this.stats.calls_today || 0;
        this.avgDurationElement.textContent = this.stats.avg_duration || 0;
    }
    
    /**
     * Fetch CDR records from API with current filters and pagination
     */
    async fetchRecords() {
        this.showLoading(true);
        
        try {
            // Calculate offset based on current page
            const offset = (this.currentPage - 1) * this.recordsPerPage;
            
            // Build query parameters
            const params = new URLSearchParams();
            params.append('limit', this.recordsPerPage);
            params.append('offset', offset);
            
            // Add filters if they exist
            if (this.filters.start_date) params.append('start_date', this.filters.start_date);
            if (this.filters.end_date) params.append('end_date', this.filters.end_date);
            if (this.filters.src) params.append('src', this.filters.src);
            if (this.filters.dst) params.append('dst', this.filters.dst);
            if (this.filters.disposition) params.append('disposition', this.filters.disposition);
            
            // Fetch data
            const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/cdr?${params.toString()}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.records = data.records;
                this.totalRecords = data.count;
                this.updateRecordsDisplay();
                this.updatePagination();
            } else {
                console.error('Error fetching CDR records:', data);
                this.showNoRecords(true);
            }
        } catch (error) {
            console.error('Error fetching CDR records:', error);
            this.showNoRecords(true);
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * Update the records table with current data
     */
    updateRecordsDisplay() {
        // Clear existing rows
        this.cdrTable.innerHTML = '';
        
        // Show/hide no records message
        if (this.records.length === 0) {
            this.showNoRecords(true);
            return;
        } else {
            this.showNoRecords(false);
        }
        
        // Update records count display
        this.recordsShowing.textContent = this.records.length;
        this.recordsTotal.textContent = this.totalRecords;
        
        // Add rows for each record
        this.records.forEach(record => {
            const row = document.createElement('tr');
            
            // Format start time
            const startTime = record.start ? new Date(record.start) : null;
            const formattedStartTime = startTime ? 
                `${startTime.toLocaleDateString()} ${startTime.toLocaleTimeString()}` : 
                'N/A';
            
            // Format duration and billsec
            const duration = record.duration || 0;
            const billsec = record.billsec || 0;
            
            // Create row content
            row.innerHTML = `
                <td>${formattedStartTime}</td>
                <td>${formatExtension(record.src)}</td>
                <td>${formatExtension(record.dst)}</td>
                <td>${formatDuration(duration)}</td>
                <td>${formatDuration(billsec)}</td>
                <td><span class="badge ${this.getDispositionBadgeClass(record.disposition)}">${record.disposition || 'Unknown'}</span></td>
                <td>${record.channel || 'N/A'}</td>
            `;
            
            this.cdrTable.appendChild(row);
        });
    }
    
    /**
     * Get the appropriate badge class for a call disposition
     * @param {string} disposition - The call disposition
     * @returns {string} - The CSS class for the badge
     */
    getDispositionBadgeClass(disposition) {
        switch (disposition) {
            case 'ANSWERED':
                return 'bg-success';
            case 'NO ANSWER':
                return 'bg-warning text-dark';
            case 'BUSY':
                return 'bg-info';
            case 'FAILED':
                return 'bg-danger';
            default:
                return 'bg-secondary';
        }
    }
    
    /**
     * Update pagination controls
     */
    updatePagination() {
        // Clear existing pagination
        this.pagination.innerHTML = '';
        
        // Calculate total pages
        const totalPages = Math.ceil(this.totalRecords / this.recordsPerPage);
        
        // Don't show pagination if there's only one page
        if (totalPages <= 1) {
            return;
        }
        
        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a>`;
        prevLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage > 1) {
                this.currentPage--;
                this.fetchRecords();
            }
        });
        this.pagination.appendChild(prevLi);
        
        // Page numbers
        let startPage = Math.max(1, this.currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        
        // Adjust start page if we're near the end
        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageLi.addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = i;
                this.fetchRecords();
            });
            this.pagination.appendChild(pageLi);
        }
        
        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${this.currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#" aria-label="Next"><span aria-hidden="true">&raquo;</span></a>`;
        nextLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage < totalPages) {
                this.currentPage++;
                this.fetchRecords();
            }
        });
        this.pagination.appendChild(nextLi);
    }
    
    /**
     * Show or hide the loading indicator
     * @param {boolean} show - Whether to show the loading indicator
     */
    showLoading(show) {
        this.loadingIndicator.style.display = show ? 'block' : 'none';
    }
    
    /**
     * Show or hide the no records message
     * @param {boolean} show - Whether to show the no records message
     */
    showNoRecords(show) {
        this.noRecordsMessage.classList.toggle('d-none', !show);
    }
    
    /**
     * Export current records to CSV file
     */
    exportToCSV() {
        if (this.records.length === 0) {
            alert('No records to export');
            return;
        }
        
        // CSV header
        let csvContent = 'Date,Time,From,To,Duration,Billable,Status,Channel\n';
        
        // Add each record
        this.records.forEach(record => {
            const startTime = record.start ? new Date(record.start) : null;
            const date = startTime ? startTime.toLocaleDateString() : 'N/A';
            const time = startTime ? startTime.toLocaleTimeString() : 'N/A';
            
            // Format fields and escape commas
            const row = [
                date,
                time,
                record.src || '',
                record.dst || '',
                record.duration || 0,
                record.billsec || 0,
                record.disposition || 'Unknown',
                (record.channel || '').replace(/,/g, ';') // Replace commas in channel name
            ];
            
            // Add row to CSV content
            csvContent += row.join(',') + '\n';
        });
        
        // Create download link
        const encodedUri = encodeURI('data:text/csv;charset=utf-8,' + csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', `cdr_export_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        
        // Trigger download and clean up
        link.click();
        document.body.removeChild(link);
    }
}

/**
 * Format duration in seconds to a readable format
 * @param {number} seconds - Duration in seconds
 * @returns {string} - Formatted duration string
 */
function formatDuration(seconds) {
    if (!seconds) return '0s';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    let result = '';
    if (hours > 0) result += `${hours}h `;
    if (minutes > 0 || hours > 0) result += `${minutes}m `;
    result += `${remainingSeconds}s`;
    
    return result;
}

/**
 * Format extension number with caller ID if available
 * @param {string} extension - Extension number or caller ID string
 * @returns {string} - Formatted extension string
 */
function formatExtension(extension) {
    if (!extension) return 'Unknown';
    
    // Check if it's a caller ID format like "Name" <number>
    const match = extension.match(/"([^"]+)"\s*<(\d+)>/);
    if (match) {
        const [_, name, number] = match;
        return `${name} (${number})`;
    }
    
    return extension;
}

// Initialize CDR manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on the CDR page
    if (document.getElementById('cdr-table')) {
        window.cdrManager = new CDRManager();
    }
});
