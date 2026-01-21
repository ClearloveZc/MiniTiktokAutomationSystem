"""
Browser Management Module
Handles browser initialization and configuration with anti-detection features.
"""

import os
from pathlib import Path
from typing import Optional, Union

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.file_detector import LocalFileDetector
from loguru import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BrowserManager:
    """Manages browser instance with anti-detection capabilities."""
    
    def __init__(self, config: dict):
        """
        Initialize BrowserManager.
        
        Args:
            config: Browser configuration dictionary
        """
        self.config = config
        self.driver: Optional[Union[uc.Chrome, webdriver.Chrome]] = None
        
    def create_driver(self) -> Union[uc.Chrome, webdriver.Chrome]:
        """
        Create and configure Chrome driver with anti-detection.
        
        Returns:
            Configured Chrome WebDriver instance
        """
        logger.info("Initializing Chrome browser...")
        
        options = uc.ChromeOptions()
        
        # Window size
        width = self.config.get("window_size", {}).get("width", 1920)
        height = self.config.get("window_size", {}).get("height", 1080)
        options.add_argument(f"--window-size={width},{height}")
        
        # Headless mode with additional settings to avoid detection
        if self.config.get("headless", False):
            options.add_argument("--headless=new")
            # Additional settings for headless mode
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--disable-features=VizDisplayCompositor")
            # Set user agent to avoid headless detection
            user_agent = self.config.get("user_agent", 
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_argument(f"--user-agent={user_agent}")
            logger.info("Running in headless mode")
        
        # User data directory for persistent login (REQUIRED for session persistence)
        # Priority: environment variable > config file > default path
        user_data_dir = (
            os.environ.get("CHROME_USER_DATA_DIR") or 
            self.config.get("user_data_dir") or 
            "./chrome_data"
        )
        user_data_path = Path(user_data_dir).resolve()
        user_data_path.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={user_data_path}")
        logger.info(f"Using user data directory: {user_data_path}")
        
        # Additional options for stability
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Create driver
        # Check if using remote Selenium (Docker with selenium/standalone-chrome)
        selenium_url = os.environ.get("SELENIUM_REMOTE_URL")
        if selenium_url:
            # Docker mode: connect to remote Selenium with retry
            logger.info(f"Using remote Selenium at {selenium_url}")
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--window-size={width},{height}")
            
            # Retry connection (Selenium container may need time to start)
            import time
            max_retries = 30
            for attempt in range(max_retries):
                try:
                    self.driver = webdriver.Remote(
                        command_executor=selenium_url,
                        options=chrome_options
                    )
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.info(f"Waiting for Selenium... ({attempt + 1}/{max_retries})")
                        time.sleep(2)
                    else:
                        raise Exception(f"Could not connect to Selenium after {max_retries} attempts: {e}")
            
            # Enable file upload for remote WebDriver
            self.driver.file_detector = LocalFileDetector()
            self.is_remote = True
        else:
            # Local: use undetected-chromedriver for anti-detection
            self.driver = uc.Chrome(options=options)
            self.is_remote = False
        
        # Set timeouts
        self.driver.implicitly_wait(self.config.get("implicit_wait", 10))
        self.driver.set_page_load_timeout(self.config.get("page_load_timeout", 60))
        
        logger.success("Browser initialized successfully")
        return self.driver
    
    def close(self):
        """Close the browser and clean up resources."""
        if self.driver:
            logger.info("Closing browser...")
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            self.driver = None
