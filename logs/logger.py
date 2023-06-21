import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
# Create file handler
file_handler = RotatingFileHandler(
                'logs/converse.log',
                maxBytes=1024 * 1024 * 5, # 5 MB
                backupCount=5
            )
file_handler.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to handlers
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)