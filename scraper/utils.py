import logging
from logging.handlers import RotatingFileHandler

################# LOGGER ########################

file_handler = RotatingFileHandler(
    "app.log",
    maxBytes=1024 * 1024 * 5,  #5 megabytes
    backupCount=3,
    encoding='utf-8'
)

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s',  # Log message format
    handlers=[
        file_handler,  # Write logs to a file
        logging.StreamHandler()  # Print logs to the console
    ]
)

logger = logging.getLogger(__name__)

#################################################