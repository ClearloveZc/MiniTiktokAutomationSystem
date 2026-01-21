"""
Export Cookies Script
Login to TikTok and save cookies for Docker deployment.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from browser import BrowserManager
from login import LoginManager
from utils import load_config, setup_logging
from loguru import logger


def main():
    config = load_config("config/config.yaml")
    setup_logging(config.get("logging", {}))
    
    logger.info("=" * 60)
    logger.info("TikTok Cookie Exporter")
    logger.info("=" * 60)
    logger.info("")
    logger.info("This will open a browser for you to login to TikTok.")
    logger.info("After login, cookies will be saved for Docker use.")
    logger.info("")
    
    browser_manager = None
    try:
        browser_manager = BrowserManager(config["browser"])
        driver = browser_manager.create_driver()
        
        login_manager = LoginManager(driver, config)
        
        # Navigate to TikTok
        logger.info("Opening TikTok...")
        driver.get("https://www.tiktok.com/login")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Please login to TikTok in the browser window.")
        logger.info("Press Enter here after you've logged in.")
        logger.info("=" * 60)
        logger.info("")
        
        input("Press Enter after you've logged in... ")
        
        # Wait a moment for session to stabilize
        time.sleep(2)
        
        # Save cookies
        cookie_file = "data/cookies/tiktok_cookies.json"
        if login_manager.save_cookies(cookie_file):
            logger.success(f"Cookies saved to {cookie_file}")
            logger.info("")
            logger.info("You can now use Docker with these cookies:")
            logger.info("  docker-compose run tiktok-auto python src/main.py ...")
        else:
            logger.error("Failed to save cookies")
            return 1
            
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
