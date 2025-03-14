import os
import logging
from datetime import datetime

def setup_logger(name, log_dir="logs", level=logging.INFO):
    """Set up a logger with file and console handlers"""
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create file handler
    log_filename = f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(os.path.join(log_dir, log_filename))
    file_handler.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger