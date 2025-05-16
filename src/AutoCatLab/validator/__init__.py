"""Validation module for AutoCatLab."""
from pathlib import Path

def validate_config_path(file_path: str) -> Path:
    """Validate and convert configuration file path to absolute path.
    
    Args:
        file_path (str): Path to the configuration file
        
    Returns:
        Path: Absolute path to the configuration file
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
    """
    config_path = Path(file_path)
    if not config_path.is_absolute():
        config_path = Path.cwd() / file_path
        
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
    return config_path 
