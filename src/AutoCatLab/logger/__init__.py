"""Logging module for AutoCatLab."""
import logging
from pathlib import Path
from typing import Dict, Any

def setup_logger(config: Dict[str, Any]) -> logging.Logger:
    """Setup logger with file and console handlers.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory in workflow output directory
    log_dir = Path(config['workflow_output_directory']) / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('autocatlab')
    logger.setLevel(logging.INFO)
    
    # Create file handler
    log_file = log_dir / 'workflow.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 