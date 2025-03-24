import asyncio
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

# Set up logging to use backend/logs directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BACKEND_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Change working directory to backend root to ensure relative paths work
os.chdir(BACKEND_DIR)

# Now import ami_client after setting up paths
from ami.client import AmiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EndpointMonitor:
    def __init__(self, host: str = '127.0.0.1', port: int = 5038,
                 username: str = 'admin', password: str = 'admin'):
        """Initialize endpoint monitor
        
        Args:
            host: AMI server hostname
            port: AMI server port
            username: AMI username
            password: AMI password
        """
        self.endpoint_states: Dict[str, Dict] = {}
        self.ami = AmiClient(
            host=host,
            port=port,
            username=username,
            password=password,
            event_callback=self._handle_event
        )
        
    async def connect(self):
        """Establish connection to AMI"""
        await self.ami.connect()
        
    async def start_monitoring(self, extensions: List[str]):
        """Start monitoring specific extensions
        
        Args:
            extensions: List of extension numbers to monitor
        """
        # Get initial state for all extensions
        for extension in extensions:
            await self._update_endpoint_state(extension)
            
    async def _update_endpoint_state(self, extension: str):
        """Update the stored state for an extension"""
        try:
            # Get endpoint details
            details = await self.ami.get_endpoint_details(extension)
            if not details or not details.get('exists_in_config', False):
                logger.warning(f"Extension {extension} not found in configuration")
                return

            # Update state
            state = await self.ami.get_endpoint_state(extension)
            registration = await self.ami.get_endpoint_registration(extension)
            
            self.endpoint_states[extension] = {
                'last_updated': datetime.now().isoformat(),
                'exists_in_config': True,
                'details': details.get('details', {}),
                'state': str(state) if state is not None else 'unknown',
                'registration': str(registration) if registration is not None else 'unknown'
            }
            
            logger.info(f"Updated state for extension {extension}:")
            logger.info(f"State: {self.endpoint_states[extension]['state']}")
            logger.info(f"Registration: {self.endpoint_states[extension]['registration']}")
            
        except Exception as e:
            logger.error(f"Error updating state for extension {extension}: {e}")
        
    async def _handle_event(self, manager, event: Dict):
        """Handle incoming AMI events
        
        Args:
            manager: The AMI manager instance
            event: The event dictionary containing event details
        """
        try:
            event_type = str(event.get('Event', ''))
            if not event_type:
                return
                
            # Handle different event types
            if event_type in ['DeviceStateChange', 'PeerStatus', 'Registry']:
                device = str(event.get('Device', '') or event.get('Peer', ''))
                if not device:
                    return
                    
                # Extract extension from device string (e.g., 'PJSIP/100' -> '100')
                extension = device.split('/')[-1]
                
                if extension in self.endpoint_states:
                    logger.info(f"Received {event_type} event for extension {extension}")
                    await self._update_endpoint_state(extension)
        except Exception as e:
            logger.error(f"Error handling event: {e}")

async def test_endpoint_monitoring():
    """Test endpoint monitoring functionality"""
    monitor = EndpointMonitor(
        host=os.getenv('ASTERISK_HOST', '127.0.0.1'),
        port=int(os.getenv('ASTERISK_AMI_PORT', '5038')),
        username=os.getenv('ASTERISK_AMI_USER', 'admin'),
        password=os.getenv('ASTERISK_AMI_PASSWORD', 'admin')
    )
    
    try:
        # Connect to AMI
        logger.info("Connecting to AMI...")
        await monitor.connect()
        logger.info("Successfully connected to AMI")
        
        # Start monitoring extensions
        extensions = ['100', '101']  # Add your extensions here
        logger.info(f"Starting monitoring for extensions: {extensions}")
        await monitor.start_monitoring(extensions)
        
        # Keep monitoring for some time
        logger.info("Monitoring events for 5 minutes...")
        await asyncio.sleep(300)  # Monitor for 5 minutes
        
    except Exception as e:
        logger.error(f"Error during monitoring: {e}")
    finally:
        await monitor.ami.close()

if __name__ == "__main__":
    asyncio.run(test_endpoint_monitoring())