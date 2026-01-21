"""
Login Module
Handles TikTok authentication via cookies or browser session.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger


class LoginManager:
    """Manages TikTok login and session handling."""
    
    COOKIE_FILE = "data/cookies/tiktok_cookies.json"
    
    def __init__(self, driver: WebDriver, config: dict):
        """
        Initialize LoginManager.
        
        Args:
            driver: Selenium WebDriver instance
            config: Application configuration
        """
        self.driver = driver
        self.config = config
        self.base_url = config.get("tiktok", {}).get("base_url", "https://www.tiktok.com")
        
    def is_logged_in(self) -> bool:
        """
        Check if user is currently logged in.
        
        Returns:
            True if logged in, False otherwise
        """
        try:
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Check for login indicators (avatar, profile elements)
            # TikTok's DOM changes frequently, so we check multiple indicators
            login_indicators = [
                '[data-e2e="profile-icon"]',
                '[data-e2e="nav-profile"]',
                'a[href*="/profile"]'
            ]
            
            for selector in login_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element:
                        logger.info("User is logged in")
                        return True
                except:
                    continue
                    
            logger.warning("User is not logged in")
            return False
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
    
    def load_cookies(self, cookie_file: Optional[str] = None) -> bool:
        """
        Load cookies from file to restore session.
        
        Args:
            cookie_file: Path to cookie file (JSON format)
            
        Returns:
            True if cookies loaded successfully
        """
        cookie_path = Path(cookie_file or self.COOKIE_FILE)
        
        if not cookie_path.exists():
            logger.warning(f"Cookie file not found: {cookie_path}")
            return False
            
        try:
            # First navigate to TikTok domain
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # Load and add cookies
            with open(cookie_path, "r") as f:
                cookies = json.load(f)
                
            for cookie in cookies:
                # Remove problematic fields
                cookie.pop("sameSite", None)
                cookie.pop("storeId", None)
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Could not add cookie: {e}")
                    
            logger.info(f"Loaded {len(cookies)} cookies from {cookie_path}")
            
            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(3)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return False
    
    def save_cookies(self, cookie_file: Optional[str] = None) -> bool:
        """
        Save current cookies to file.
        
        Args:
            cookie_file: Path to save cookies
            
        Returns:
            True if cookies saved successfully
        """
        cookie_path = Path(cookie_file or self.COOKIE_FILE)
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            cookies = self.driver.get_cookies()
            with open(cookie_path, "w") as f:
                json.dump(cookies, f, indent=2)
                
            logger.info(f"Saved {len(cookies)} cookies to {cookie_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
            return False
    
    def manual_login(self, timeout: int = 120) -> bool:
        """
        Open login page and wait for user to login manually.
        
        Args:
            timeout: Maximum time to wait for login (seconds)
            
        Returns:
            True if login successful
        """
        login_url = self.config.get("tiktok", {}).get("login_url", "https://www.tiktok.com/login")
        
        logger.info("Opening TikTok login page...")
        logger.info("Please login manually in the browser window")
        
        self.driver.get(login_url)
        
        # Wait for user to complete login
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_logged_in():
                logger.success("Login successful!")
                self.save_cookies()
                return True
            time.sleep(5)
            
        logger.error("Login timeout exceeded")
        return False
    
    def ensure_logged_in(self) -> bool:
        """
        Ensure user is logged in, trying cookies first then manual login.
        
        Returns:
            True if logged in
        """
        # Check if running in Docker (remote Selenium)
        is_docker = os.environ.get("SELENIUM_REMOTE_URL") is not None
        
        if is_docker:
            # In Docker: always load cookies first (remote browser has no session)
            logger.info("Docker mode: loading cookies...")
            if not self.load_cookies():
                logger.error("No cookies found! Run 'python src/export_cookies.py' locally first")
                return False
            
            # Verify login after loading cookies
            if self.is_logged_in():
                logger.info("Successfully logged in via cookies")
                return True
            else:
                logger.error("Cookies loaded but login failed")
                logger.error("Try re-exporting cookies with 'python src/export_cookies.py'")
                return False
        
        # Local mode: check if already logged in (via user-data-dir)
        if self.is_logged_in():
            return True
            
        # Try loading cookies
        if self.load_cookies():
            if self.is_logged_in():
                return True
                
        # Fall back to manual login (only in local mode)
        logger.info("Automatic login failed, manual login required")
        return self.manual_login()
