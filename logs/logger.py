import logging


# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Set the logging level

# Create a file handler
file_handler = logging.FileHandler('logs/votebuddy.log')
file_handler.setLevel(logging.INFO)  # Set the logging level for the file

#create debug logger
debug_logger = logging.FileHandler('logs/debug.log')
debug_logger.setLevel(logging.DEBUG)  # Set the logging level for the file

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set the logging level for the console

# Create a formatter and set it for both handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)