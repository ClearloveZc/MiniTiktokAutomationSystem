"""
Login Only Script
Opens browser for manual TikTok login and saves the session.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from browser import BrowserManager
from utils import load_config, setup_logging
from loguru import logger


def main():
    """Open browser for manual login."""
    # Load configuration
    config = load_config("config/config.yaml")
    setup_logging(config.get("logging", {}))
    
    logger.info("=" * 50)
    logger.info("TikTok Login Helper")
    logger.info("=" * 50)
    logger.info("")
    logger.info("This will open a browser for you to login to TikTok.")
    logger.info("After login, your session will be saved automatically.")
    logger.info("")
    
    browser_manager = None
    try:
        # Initialize browser
        browser_manager = BrowserManager(config["browser"])
        driver = browser_manager.create_driver()
        
        # Navigate to TikTok
        logger.info("Opening TikTok...")
        driver.get("https://www.tiktok.com/login")
        
        logger.info("")
        logger.info("=" * 50)
        logger.info("Please login to TikTok in the browser window.")
        logger.info("After you're done, press Enter here to save and exit.")
        logger.info("=" * 50)
        logger.info("")
        
        # Wait for user to login
        input("Press Enter after you've logged in... ")
        
        # Verify login by checking URL or page content
        current_url = driver.current_url
        logger.info(f"Current URL: {current_url}")
        
        if "login" not in current_url.lower():
            logger.success("Login successful! Session saved to chrome_data/")
        else:
            logger.warning("You may not be logged in yet. Session saved anyway.")
            
        logger.info("You can now run the uploader and it will use this session.")
        
    except KeyboardInterrupt:
        logger.info("\nCancelled by user")
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1
    finally:
        if browser_manager:
            logger.info("Closing browser...")
            browser_manager.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
