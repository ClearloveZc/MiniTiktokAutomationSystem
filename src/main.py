"""
TikTok Auto Publisher - Main Entry Point
"""

import argparse
from pathlib import Path
from loguru import logger

from browser import BrowserManager
from uploader import TikTokUploader
from utils import load_config, setup_logging


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="TikTok Video Auto Publisher"
    )
    parser.add_argument(
        "-v", "--video",
        type=str,
        required=True,
        help="Path to the video file to upload"
    )
    parser.add_argument(
        "-t", "--title",
        type=str,
        default="",
        help="Video title/caption"
    )
    parser.add_argument(
        "--tags",
        type=str,
        nargs="+",
        default=[],
        help="Hashtags for the video (without #)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config/config.yaml",
        help="Path to config file"
    )
    return parser.parse_args()


def main():
    """Main function to run the TikTok auto publisher."""
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config.get("logging", {}))
    
    # Validate video file
    video_path = Path(args.video)
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return 1
    
    logger.info(f"Starting TikTok Auto Publisher v0.1.0")
    logger.info(f"Video: {video_path}")
    
    # Override headless mode if specified
    if args.headless:
        config["browser"]["headless"] = True
    
    browser_manager = None
    try:
        # Initialize browser
        browser_manager = BrowserManager(config["browser"])
        driver = browser_manager.create_driver()
        
        # Create uploader and post video
        uploader = TikTokUploader(driver, config)
        success = uploader.upload_video(
            video_path=str(video_path),
            title=args.title,
            tags=args.tags
        )
        
        if success:
            logger.success("Video uploaded successfully!")
            return 0
        else:
            logger.error("Failed to upload video")
            return 1
            
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        return 1
    finally:
        if browser_manager:
            browser_manager.close()


if __name__ == "__main__":
    exit(main())
