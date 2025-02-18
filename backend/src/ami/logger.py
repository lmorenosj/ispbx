import logging
from datetime import datetime
import json

def setup_ami_loggers():
    """Configure and setup AMI-related loggers"""
    # Configure AMI client logging
    logger = logging.getLogger(__name__)
    logger.propagate = False  # Prevent logs from propagating to root logger (console)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add file handlers for general logs and AMI responses
    file_handler = logging.FileHandler('logs/ami.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    # Create a separate logger for AMI responses
    ami_response_logger = logging.getLogger('ami_responses')
    ami_response_logger.propagate = False
    ami_response_logger.setLevel(logging.INFO)

    # Add file handler for AMI responses
    response_handler = logging.FileHandler('logs/ami_responses.log')
    response_handler.setFormatter(logging.Formatter('%(asctime)s\n%(message)s\n' + '-'*80 + '\n'))
    ami_response_logger.addHandler(response_handler)

    return logger, ami_response_logger

# Initialize loggers
logger, ami_response_logger = setup_ami_loggers()
