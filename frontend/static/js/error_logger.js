// Frontend Error Logger
class ErrorLogger {
    constructor() {
        this.logFile = 'frontend_errors.log';
        this.errorCount = 0;
        this.initTime = new Date();
    }

    /**
     * Log an error with context
     * @param {string} source - Where the error occurred (e.g., 'ExtensionDetails', 'APICall')
     * @param {Error|string} error - The error object or message
     * @param {Object} context - Additional context (e.g., {extension: '100', action: 'fetch'})
     */
    logError(source, error, context = {}) {
        this.errorCount++;
        const timestamp = new Date().toISOString();
        const errorMessage = error instanceof Error ? error.message : error;
        const stackTrace = error instanceof Error ? error.stack : new Error().stack;

        const logEntry = {
            id: `ERR_${this.errorCount}`,
            timestamp,
            source,
            message: errorMessage,
            stackTrace,
            context,
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        // Log to console with formatting
        console.group(`🔴 Error #${this.errorCount} in ${source}`);
        console.error('Message:', errorMessage);
        console.log('Context:', context);
        console.log('Stack:', stackTrace);
        console.groupEnd();

        // Store in localStorage for persistence
        this.storeError(logEntry);

        // If configured, send to backend
        this.sendToBackend(logEntry);
    }

    /**
     * Store error in localStorage
     * @param {Object} logEntry - The error log entry
     */
    storeError(logEntry) {
        try {
            const key = `error_${this.initTime.getTime()}_${this.errorCount}`;
            localStorage.setItem(key, JSON.stringify(logEntry));
        } catch (e) {
            console.error('Failed to store error in localStorage:', e);
        }
    }

    /**
     * Send error to backend if configured
     * @param {Object} logEntry - The error log entry
     */
    async sendToBackend(logEntry) {
        try {
            const response = await fetch('/api/log-error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(logEntry)
            });

            if (!response.ok) {
                console.error('Failed to send error to backend:', response.statusText);
            }
        } catch (e) {
            console.error('Failed to send error to backend:', e);
        }
    }

    /**
     * Get all stored errors
     * @returns {Array} Array of error entries
     */
    getStoredErrors() {
        const errors = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith('error_')) {
                try {
                    const error = JSON.parse(localStorage.getItem(key));
                    errors.push(error);
                } catch (e) {
                    console.error('Failed to parse stored error:', e);
                }
            }
        }
        return errors;
    }

    /**
     * Clear all stored errors
     */
    clearStoredErrors() {
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith('error_')) {
                keysToRemove.push(key);
            }
        }
        keysToRemove.forEach(key => localStorage.removeItem(key));
    }
}

// Create global instance
const errorLogger = new ErrorLogger();

// Add global error handler
window.onerror = function(msg, url, lineNo, columnNo, error) {
    errorLogger.logError('GlobalError', error || msg, {
        url,
        lineNo,
        columnNo
    });
    return false;
};

// Add unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    errorLogger.logError('UnhandledPromiseRejection', event.reason, {
        promise: event.promise
    });
});
