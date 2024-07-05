import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Retrieve log level from environment or use "DEBUG" as default
log_level_name = os.environ.get("LOG_LEVEL", "DEBUG")
log_level = logging.getLevelName(log_level_name)

# Get the root logger
root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Create console handler for output to stdout
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)

# Create rotating file handler
# Adjust 'maxBytes' and 'backupCount' to your needs
LOG_FILE_FOLDER = "/var/log/rag_studio"
if not os.path.exists(LOG_FILE_FOLDER):
    os.makedirs(LOG_FILE_FOLDER)
file_handler = RotatingFileHandler(
    LOG_FILE_FOLDER + "/application.log", maxBytes=1048576, backupCount=5
)
file_handler.setLevel(log_level)

# Create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the root logger
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)
