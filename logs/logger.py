import logging
from logging.handlers import RotatingFileHandler
import sys


def get_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                'logs/app.log',
                maxBytes=1024 * 1024 * 5, # 5 MB
                backupCount=5
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)
# # Create file handler
# file_handler = WatchedFileHandler('logs/votebuddy.log')
# file_handler.setLevel(logging.DEBUG)

# # Create console handler
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)

# # Create formatter
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# # Add formatter to handlers
# file_handler.setFormatter(formatter)
# console_handler.setFormatter(formatter)

# # Add the handlers to the logger
# logger.addHandler(file_handler)
# logger.addHandler(console_handler)