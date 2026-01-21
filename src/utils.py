"""
Utility Functions
Common helper functions for the TikTok Auto Publisher.
"""

import sys
from pathlib import Path
from typing import Any, Dict

import yaml
from loguru import logger


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"Config file not found: {config_file}, using defaults")
        return get_default_config()
        
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_file}")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration.
    
    Returns:
        Default configuration dictionary
    """
    return {
        "browser": {
            "headless": False,
            "window_size": {"width": 1920, "height": 1080},
            "implicit_wait": 10,
            "page_load_timeout": 60
        },
        "tiktok": {
            "base_url": "https://www.tiktok.com",
            "upload_url": "https://www.tiktok.com/creator-center/upload",
            "login_url": "https://www.tiktok.com/login"
        },
        "upload": {
            "max_title_length": 150,
            "max_retries": 3,
            "retry_delay": 5,
            "upload_timeout": 300
        },
        "timing": {
            "min_delay": 1,
            "max_delay": 3,
            "typing_delay": 0.05
        },
        "logging": {
            "level": "INFO",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            "rotation": "10 MB",
            "retention": "7 days"
        }
    }


def setup_logging(logging_config: Dict[str, Any]):
    """
    Setup loguru logging configuration.
    
    Args:
        logging_config: Logging configuration dictionary
    """
    # Remove default handler
    logger.remove()
    
    log_format = logging_config.get(
        "format", 
        "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    log_level = logging_config.get("level", "INFO")
    
    # Console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        colorize=True
    )
    
    # File handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "tiktok_auto.log",
        format=log_format,
        level=log_level,
        rotation=logging_config.get("rotation", "10 MB"),
        retention=logging_config.get("retention", "7 days"),
        encoding="utf-8"
    )
    
    logger.info("Logging initialized")


def validate_video_file(video_path: str) -> bool:
    """
    Validate that the video file exists and has a valid format.
    
    Args:
        video_path: Path to video file
        
    Returns:
        True if video is valid
    """
    valid_extensions = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
    
    path = Path(video_path)
    
    if not path.exists():
        logger.error(f"Video file does not exist: {path}")
        return False
        
    if not path.is_file():
        logger.error(f"Path is not a file: {path}")
        return False
        
    if path.suffix.lower() not in valid_extensions:
        logger.error(f"Invalid video format: {path.suffix}")
        logger.info(f"Supported formats: {', '.join(valid_extensions)}")
        return False
        
    # Check file size (TikTok limit is typically 287.6 MB for 60-second videos)
    max_size_mb = 500
    file_size_mb = path.stat().st_size / (1024 * 1024)
    
    if file_size_mb > max_size_mb:
        logger.warning(f"Video file is large: {file_size_mb:.1f} MB")
        
    logger.info(f"Video validated: {path.name} ({file_size_mb:.1f} MB)")
    return True
