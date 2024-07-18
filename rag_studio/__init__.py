import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import List

# Retrieve log level from environment or use "DEBUG" as default
log_level_name = os.environ.get("LOG_LEVEL", "DEBUG")
log_level = logging.getLevelName(log_level_name)

# Get the root logger
root_logger = logging.getLogger()
root_logger.setLevel(log_level)


# Create console handler for output to stdout
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)

# Create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

all_handlers: List[logging.Handler] = [console_handler]
LOG_FILE_FOLDER = "/var/log/rag_studio"
if os.environ.get("DISABLE_FILE_LOGGING") != "1":
    # Create rotating file handler
    # Adjust 'maxBytes' and 'backupCount' to your needs
    if not os.path.exists(LOG_FILE_FOLDER):
        os.makedirs(LOG_FILE_FOLDER)
    file_handler = RotatingFileHandler(
        LOG_FILE_FOLDER + "/application.log", maxBytes=1048576, backupCount=5
    )
    file_handler.setLevel(log_level)

    # Add formatter
    file_handler.setFormatter(formatter)

    # Add file handler to the root logger
    all_handlers.append(file_handler)


def attach_handlers(logger):
    for handler in all_handlers:
        logger.addHandler(handler)


# Attach handlers to the root logger
attach_handlers(root_logger)
