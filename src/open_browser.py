"""
Open browser to view TikTok profile.
Press Ctrl+C to close.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from browser import BrowserManager
from utils import load_config, setup_logging
from loguru import logger


def main():
    config = load_config("config/config.yaml")
    setup_logging(config.get("logging", {}))
    
    logger.info("Opening TikTok in browser...")
    logger.info("Press Ctrl+C to close when you're done.")
    
    browser_manager = None
    try:
        browser_manager = BrowserManager(config["browser"])
        driver = browser_manager.create_driver()
        
        # Go to TikTok profile page
        driver.get("https://www.tiktok.com/profile")
        
        logger.info("Browser is open. Press Ctrl+C to close.")
        
        # Keep browser open
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\nClosing browser...")
    finally:
        if browser_manager:
            browser_manager.close()


if __name__ == "__main__":
    main()
