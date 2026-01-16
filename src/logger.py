"""Global logging configuration for the voice assistant."""
import logging
import sys

# Create the root logger for the application
logger = logging.getLogger("voice_assistant")


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the application.
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set level for our logger
    logger.setLevel(level)
