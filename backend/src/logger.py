import logging
import os
from datetime import datetime
import json
from typing import Any, Dict, Optional

class APILogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up file handler for general logs
        self.general_logger = logging.getLogger('api_general')
        self.general_logger.setLevel(logging.INFO)
        
        general_handler = logging.FileHandler(os.path.join(log_dir, 'api.log'))
        general_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.general_logger.addHandler(general_handler)
        
        # Set up file handler for errors
        self.error_logger = logging.getLogger('api_errors')
        self.error_logger.setLevel(logging.ERROR)
        
        error_handler = logging.FileHandler(os.path.join(log_dir, 'errors.log'))
        error_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s\n%(exc_info)s')
        )
        self.error_logger.addHandler(error_handler)
        
        # Set up file handler for AMI events
        self.ami_logger = logging.getLogger('ami_events')
        self.ami_logger.setLevel(logging.INFO)
        
        ami_handler = logging.FileHandler(os.path.join(log_dir, 'ami_events.log'))
        ami_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        self.ami_logger.addHandler(ami_handler)

    def log_request(self, 
                   endpoint: str, 
                   method: str, 
                   params: Optional[Dict[str, Any]] = None,
                   status_code: Optional[int] = None,
                   error: Optional[Exception] = None) -> None:
        """
        Log API request details
        
        Args:
            endpoint: The API endpoint that was called
            method: HTTP method used (GET, POST, etc.)
            params: Request parameters or body
            status_code: HTTP status code of the response
            error: Exception if one occurred
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'params': params,
            'status_code': status_code
        }
        
        if error:
            log_entry['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': getattr(error, '__traceback__', None)
            }
            self.error_logger.error(
                f"API Error - {endpoint}",
                extra={'log_entry': json.dumps(log_entry, default=str)},
                exc_info=error
            )
        else:
            self.general_logger.info(
                f"API Request - {endpoint}",
                extra={'log_entry': json.dumps(log_entry, default=str)}
            )

    def log_ami_event(self, 
                     event_type: str, 
                     event_data: Dict[str, Any],
                     error: Optional[Exception] = None) -> None:
        """
        Log AMI events and related errors
        
        Args:
            event_type: Type of AMI event
            event_data: Event data/parameters
            error: Exception if one occurred during event handling
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'event_data': event_data
        }
        
        if error:
            log_entry['error'] = {
                'type': type(error).__name__,
                'message': str(error)
            }
            self.error_logger.error(
                f"AMI Event Error - {event_type}",
                extra={'log_entry': json.dumps(log_entry, default=str)},
                exc_info=error
            )
        else:
            self.ami_logger.info(
                f"AMI Event - {event_type}",
                extra={'log_entry': json.dumps(log_entry, default=str)}
            )

    def log_error(self, 
                 error: Exception,
                 context: Optional[Dict[str, Any]] = None,
                 source: str = "UNKNOWN") -> None:
        """
        Log an error with context
        
        Args:
            error: The exception that occurred
            context: Additional context about when/where the error occurred
            source: Source of the error (e.g., 'AMI', 'API', 'Database')
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }
        
        self.error_logger.error(
            f"Error in {source}",
            extra={'log_entry': json.dumps(log_entry, default=str)},
            exc_info=error
        )

    def get_recent_errors(self, n: int = 10) -> list:
        """
        Get the n most recent errors from the error log
        
        Args:
            n: Number of recent errors to retrieve
            
        Returns:
            List of the n most recent error log entries
        """
        errors = []
        error_log_path = os.path.join(self.log_dir, 'errors.log')
        
        if os.path.exists(error_log_path):
            with open(error_log_path, 'r') as f:
                # Read all lines and split into error entries
                lines = f.readlines()
                current_error = []
                
                for line in lines:
                    if line.startswith('20'):  # New error entry (starts with year)
                        if current_error:
                            errors.append(''.join(current_error))
                        current_error = [line]
                    else:
                        current_error.append(line)
                
                if current_error:
                    errors.append(''.join(current_error))
        
        return errors[-n:]  # Return only the n most recent errors

# Create a global instance
api_logger = APILogger()
