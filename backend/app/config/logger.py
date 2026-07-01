import sys
from loguru import logger
from app.config.settings import settings

def setup_logging():
    """
    Configures Loguru for application-wide logging.
    Replaces standard logging to provide structured, colorized, and async-ready logs.
    """
    # Remove default handler
    logger.remove()

    # Add console handler with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.DEBUG else "INFO",
        enqueue=True, # Async safe
    )

    # Add file handler for production auditing (Rotating logs)
    logger.add(
        "logs/modelrouter.log",
        rotation="10 MB",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        enqueue=True,
        compression="zip"
    )

    logger.info("Loguru Logger initialized successfully.")
