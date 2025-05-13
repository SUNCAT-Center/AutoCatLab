"""Utility functions for AutoCatLab."""
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any
from typing import Optional
from typing import Union


def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """Copy a file from source to destination.
    
    Args:
        src (Union[str, Path]): Source file path
        dst (Union[str, Path]): Destination file path
        
    Raises:
        FileNotFoundError: If source file does not exist
        OSError: If copy operation fails
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    if not src_path.exists():
        raise FileNotFoundError(f"Source file does not exist: {src}")
        
    # Create destination directory if it doesn't exist
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.copy2(src_path, dst_path)

def create_directory(path: Union[str, Path]) -> None:
    """Create directory for given path if it doesn't exist.
    
    Args:
        path (Union[str, Path]): Path to create directory for
        
    Raises:
        OSError: If directory creation fails
    """
    dir_path = Path(path)
    if not dir_path.is_file():
        dir_path.mkdir(parents=True, exist_ok=True)
    else:
        dir_path.parent.mkdir(parents=True, exist_ok=True)

def setup_logger(config: Dict) -> logging.Logger:
    """Setup and configure logger.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured logger instance
    """
    # Create log directory if it doesn't exist
    log_dir = Path(config['workflow_output_directory']) / 'log'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create file handler with timestamp in filename
    log_file = log_dir / 'autocatlab.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Create formatter that includes timestamp and file/class name
    formatter = logging.Formatter('%(asctime)s - %(pathname)s:%(lineno)d - %(funcName)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger = logging.getLogger('autocatlab')
    logger.setLevel(logging.INFO)
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger 

def load_config(config_path: Optional[str] = None) -> Dict:
    """Load configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    if not config_path:
        raise ValueError("Config path is required")
        
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_file) as f:
        return json.load(f)


def load_default_config() -> Dict[str, Any]:
    """Load default configuration from config.json."""
    config_path = Path(__file__).parent / 'config.json'
    if not config_path.exists():
        raise FileNotFoundError(f"Default configuration file not found at {config_path}")

    with open(config_path, 'r') as f:
        return json.load(f)


def load_custom_config(config_path: Path) -> Dict[str, Any]:
    """Load custom configuration from specified path."""
    with open(config_path, 'r') as f:
        return json.load(f)


def merge_configs(default_config: Dict[str, Any], custom_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge custom config with default config, overriding default values."""
    merged = default_config.copy()

    def deep_merge(d1: Dict[str, Any], d2: Dict[str, Any]) -> None:
        for key, value in d2.items():
            if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
                deep_merge(d1[key], value)
            else:
                d1[key] = value

    deep_merge(merged, custom_config)
    return merged


def get_config(config_path: Path = None) -> Dict[str, Any]:
    default_config = load_default_config()

    if config_path is None:
        return default_config
    
    custom_config = load_custom_config(config_path)
    custom_config['config_path'] = config_path.absolute()
    return merge_configs(default_config, custom_config)