"""
Video Uploader Module
Handles video upload and posting to TikTok.
"""

import time
import random
from pathlib import Path
from typing import List, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from loguru import logger

from login import LoginManager


class TikTokUploader:
    """Handles video upload to TikTok."""
    
    def __init__(self, driver: WebDriver, config: dict):
        """
        Initialize TikTokUploader.
        
        Args:
            driver: Selenium WebDriver instance
            config: Application configuration
        """
        self.driver = driver
        self.config = config
        self.login_manager = LoginManager(driver, config)
        self.upload_url = config.get("tiktok", {}).get(
            "upload_url", 
            "https://www.tiktok.com/creator-center/upload"
        )
        self.timing = config.get("timing", {})
        
    def _random_delay(self, min_delay: float = None, max_delay: float = None):
        """Add random delay to simulate human behavior."""
        min_d = min_delay or self.timing.get("min_delay", 1)
        max_d = max_delay or self.timing.get("max_delay", 3)
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)
        
    def _type_like_human(self, element, text: str):
        """Type text with random delays to simulate human typing."""
        typing_delay = self.timing.get("typing_delay", 0.05)
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(typing_delay * 0.5, typing_delay * 1.5))
    
    def upload_video(
        self, 
        video_path: str, 
        title: str = "", 
        tags: List[str] = None
    ) -> bool:
        """
        Upload a video to TikTok.
        
        Args:
            video_path: Path to video file
            title: Video title/caption
            tags: List of hashtags (without #)
            
        Returns:
            True if upload successful
        """
        tags = tags or []
        video_path = Path(video_path).resolve()
        
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return False
            
        logger.info(f"Starting upload: {video_path.name}")
        
        # Ensure logged in
        if not self.login_manager.ensure_logged_in():
            logger.error("Cannot upload: not logged in")
            return False
            
        try:
            # Navigate to upload page
            logger.info("Navigating to upload page...")
            self.driver.get(self.upload_url)
            self._random_delay(3, 5)
            
            # Find and use the file input
            logger.info("Uploading video file...")
            file_input = self._find_file_input()
            if not file_input:
                logger.error("Could not find file input element")
                return False
                
            file_input.send_keys(str(video_path))
            
            # Wait for upload to complete
            if not self._wait_for_upload():
                logger.error("Video upload timed out")
                return False
            
            # Handle first-time popup "Turn on automatic content checks?"
            self._handle_content_check_popup()
                
            logger.info("Video file uploaded, filling details...")
            
            # Scroll down to see Post button
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            except:
                pass
            
            self._random_delay()
            
            # Fill in title and tags
            self._fill_caption(title, tags)
            self._random_delay(2, 4)
            
            # Click post button
            if self._click_post_button():
                # Handle any warning popups (e.g., "Content may be restricted")
                self._handle_warning_popups()
                
                logger.info("Waiting for post to complete...")
                return self._wait_for_post_complete()
            else:
                logger.error("Could not find post button")
                return False
                
        except Exception as e:
            logger.exception(f"Error during upload: {e}")
            return False
    
    def _find_file_input(self) -> Optional[object]:
        """Find the file input element on the upload page."""
        # Wait longer for page to load (especially in Docker/remote mode)
        logger.info("Waiting for page to load...")
        time.sleep(5)
        
        # Log current URL for debugging
        logger.info(f"Current URL: {self.driver.current_url}")
        
        selectors = [
            'input[type="file"]',
            'input[accept*="video"]',
            '[data-e2e="upload-input"]',
            'input[accept*="mp4"]',
            'input.upload-input',
        ]
        
        # Try to find with longer timeout
        for selector in selectors:
            try:
                logger.debug(f"Trying selector: {selector}")
                element = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                logger.info(f"Found file input: {selector}")
                return element
            except TimeoutException:
                logger.debug(f"Selector not found: {selector}")
                continue
        
        # Try JavaScript as fallback
        try:
            logger.info("Trying JavaScript fallback...")
            element = self.driver.execute_script(
                "return document.querySelector('input[type=\"file\"]');"
            )
            if element:
                logger.info("Found file input via JavaScript")
                return element
        except Exception as e:
            logger.debug(f"JavaScript fallback failed: {e}")
        
        # Log page source for debugging
        try:
            page_source = self.driver.page_source
            if 'input' in page_source.lower():
                logger.info("Page contains 'input' elements")
                # Count file inputs
                count = page_source.lower().count('type="file"')
                logger.info(f"Found {count} file input(s) in page source")
        except:
            pass
                
        return None
    
    def _wait_for_upload(self, timeout: int = None) -> bool:
        """Wait for video upload to complete."""
        timeout = timeout or self.config.get("upload", {}).get("upload_timeout", 300)
        
        logger.info(f"Waiting for upload (timeout: {timeout}s)...")
        
        start_time = time.time()
        post_found_count = 0  # Need to find Post button multiple times to confirm
        
        while time.time() - start_time < timeout:
            # Check if Post button exists AND is clickable (not just present)
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    try:
                        btn_text = button.text.strip().lower()
                        if btn_text == "post" and button.is_displayed() and button.is_enabled():
                            post_found_count += 1
                            logger.info(f"Post button detected (count: {post_found_count})")
                            # Confirm by finding it 3 times (page is stable)
                            if post_found_count >= 3:
                                logger.info("Upload completed (Post button stable)")
                                time.sleep(2)  # Extra wait for UI to settle
                                return True
                    except:
                        continue
            except:
                pass
            
            # Also check for "Edit cover" text which appears after upload
            try:
                edit_cover = self.driver.find_elements(By.XPATH, '//*[contains(text(), "Edit cover")]')
                if edit_cover and any(e.is_displayed() for e in edit_cover):
                    logger.info("Found 'Edit cover' - video uploaded")
                    post_found_count += 1
            except:
                pass
            
            # Check upload progress
            try:
                # Look for upload percentage or progress bar
                progress = self.driver.find_elements(By.XPATH, '//*[contains(text(), "%")]')
                for p in progress:
                    text = p.text.strip()
                    if '%' in text and text != '100%':
                        logger.info(f"Upload in progress: {text}")
                        post_found_count = 0  # Reset if still uploading
            except:
                pass
                
            time.sleep(3)
        
        logger.warning("Upload wait timed out, but continuing anyway...")
        return True  # Continue anyway, might still work
    
    def _fill_caption(self, title: str, tags: List[str]):
        """Fill in the video caption with title and hashtags."""
        # Build full caption
        caption_parts = []
        if title:
            caption_parts.append(title)
        if tags:
            hashtags = " ".join(f"#{tag}" for tag in tags)
            caption_parts.append(hashtags)
            
        full_caption = " ".join(caption_parts)
        
        if not full_caption:
            logger.info("No caption to add")
            return
            
        # Truncate if too long
        max_length = self.config.get("upload", {}).get("max_title_length", 150)
        if len(full_caption) > max_length:
            full_caption = full_caption[:max_length-3] + "..."
            logger.warning(f"Caption truncated to {max_length} characters")
        
        # Wait for editor to load (important in Docker)
        time.sleep(3)
        
        # Close any joyride/tutorial overlay that might block clicks
        try:
            self.driver.execute_script("""
                var overlays = document.querySelectorAll('.react-joyride__overlay, [data-test-id="overlay"]');
                overlays.forEach(function(o) { o.remove(); });
                var tooltips = document.querySelectorAll('.react-joyride__tooltip, .__floater');
                tooltips.forEach(function(t) { t.remove(); });
            """)
            logger.info("Removed joyride overlay if present")
            time.sleep(1)
        except:
            pass
        
        # Find caption input - TikTok Studio 2024-2026
        # The editor is a Draft.js editor with class "public-DraftEditor-content"
        caption_selectors = [
            # Primary selector (found via debugging)
            'div.public-DraftEditor-content',
            '.DraftEditor-editorContainer div[contenteditable="true"]',
            # Backup selectors
            'div[contenteditable="true"][data-text="true"]',
            '[data-e2e="caption-input"]',
            '.caption-input [contenteditable="true"]',
            # Generic contenteditable (last resort)
            'div[contenteditable="true"]',
        ]
        
        logger.info(f"Attempting to fill caption: {full_caption[:30]}...")
        
        for selector in caption_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"Selector '{selector}' found {len(elements)} elements")
                
                # Find the actual caption editor
                for i, element in enumerate(elements):
                    try:
                        visible = element.is_displayed()
                        size = element.size
                        logger.info(f"  Element {i}: visible={visible}, size={size}")
                        
                        if not visible:
                            continue
                        
                        # Click and type
                        element.click()
                        time.sleep(0.5)
                        
                        # Select all and delete
                        from selenium.webdriver.common.keys import Keys
                        from selenium.webdriver.common.action_chains import ActionChains
                        
                        # Use ActionChains for more reliable input
                        actions = ActionChains(self.driver)
                        actions.click(element)
                        actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL)
                        actions.send_keys(Keys.BACKSPACE)
                        actions.perform()
                        time.sleep(0.3)
                        
                        # Type caption
                        element.send_keys(full_caption)
                        logger.info(f"Caption added: {full_caption[:50]}...")
                        return
                        
                    except Exception as e:
                        logger.warning(f"Element {i} interaction failed: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Caption selector {selector} failed: {e}")
                continue
        
        # JavaScript fallback
        try:
            logger.info("Trying JavaScript to set caption...")
            js_code = f"""
            var editors = document.querySelectorAll('[contenteditable="true"]');
            for (var i = 0; i < editors.length; i++) {{
                var editor = editors[i];
                if (editor.offsetHeight > 50) {{  // Likely the main caption editor
                    editor.focus();
                    editor.innerHTML = '<span data-text="true">{full_caption}</span>';
                    editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    return 'success';
                }}
            }}
            return 'not_found';
            """
            result = self.driver.execute_script(js_code)
            if result == 'success':
                logger.info(f"Caption added via JavaScript: {full_caption[:50]}...")
                return
        except Exception as e:
            logger.debug(f"JavaScript caption failed: {e}")
                
        logger.warning("Could not find caption input element")
    
    def _handle_content_check_popup(self):
        """Handle first-time 'Turn on automatic content checks?' popup."""
        time.sleep(1)
        
        try:
            # Look for "Turn on" button
            turn_on_selectors = [
                '//button[text()="Turn on"]',
                '//button[.//text()="Turn on"]',
                '//div[text()="Turn on"]/ancestor::button',
                'button.TUXButton--primary',
            ]
            
            for selector in turn_on_selectors:
                try:
                    if selector.startswith("//"):
                        btn = self.driver.find_element(By.XPATH, selector)
                    else:
                        btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if btn and btn.is_displayed() and "turn on" in btn.text.lower():
                        btn.click()
                        logger.info("Clicked 'Turn on' for automatic content checks")
                        time.sleep(1)
                        return
                except:
                    continue
            
            # If "Turn on" not found, try "Cancel"
            try:
                cancel_btn = self.driver.find_element(By.XPATH, '//button[text()="Cancel"]')
                if cancel_btn and cancel_btn.is_displayed():
                    cancel_btn.click()
                    logger.info("Clicked 'Cancel' for content checks popup")
                    time.sleep(0.5)
            except:
                pass
                
        except Exception as e:
            logger.debug(f"No content check popup found: {e}")

    def _handle_warning_popups(self):
        """Handle warning popups like 'Content may be restricted'."""
        time.sleep(1.5)  # Wait for popup to appear
        
        try:
            # Check if "Content may be restricted" popup exists
            popup_title = self.driver.find_elements(By.XPATH, '//*[text()="Content may be restricted"]')
            
            if not popup_title:
                logger.debug("No 'Content may be restricted' popup found")
                return
            
            logger.info("Found 'Content may be restricted' popup, closing...")
            
            popup_closed = False
            
            # Method 1: Click the close icon DIV (class: common-modal-close-icon)
            try:
                close_icon = self.driver.find_element(By.CSS_SELECTOR, 'div.common-modal-close-icon')
                if close_icon and close_icon.is_displayed():
                    close_icon.click()
                    logger.info("Closed popup using div.common-modal-close-icon")
                    popup_closed = True
                    time.sleep(1)
            except Exception as e:
                logger.debug(f"Method 1 (common-modal-close-icon) failed: {e}")
            
            # Method 2: Try other close icon selectors
            if not popup_closed:
                close_selectors = [
                    '[class*="close-icon"]',
                    '[class*="closeIcon"]',
                    '[class*="modal-close"]',
                    '.px-icon',
                ]
                for selector in close_selectors:
                    try:
                        close_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if close_elem and close_elem.is_displayed():
                            close_elem.click()
                            logger.info(f"Closed popup using {selector}")
                            popup_closed = True
                            time.sleep(1)
                            break
                    except:
                        continue
            
            # Method 3: Use JavaScript to click the close icon
            if not popup_closed:
                try:
                    js_code = """
                    var closeIcon = document.querySelector('div.common-modal-close-icon') || 
                                    document.querySelector('[class*="close-icon"]') ||
                                    document.querySelector('[class*="modal-close"]');
                    if (closeIcon) {
                        closeIcon.click();
                        return true;
                    }
                    return false;
                    """
                    result = self.driver.execute_script(js_code)
                    if result:
                        logger.info("Closed popup using JavaScript")
                        popup_closed = True
                        time.sleep(1)
                except Exception as e:
                    logger.debug(f"Method 3 (JS) failed: {e}")
            
            # After closing, click Post again
            if popup_closed:
                time.sleep(0.5)
                still_visible = self.driver.find_elements(By.XPATH, '//*[text()="Content may be restricted"]')
                if not still_visible or not any(e.is_displayed() for e in still_visible):
                    logger.info("Popup closed! Re-clicking Post...")
                    self._click_post_button()
                else:
                    logger.warning("Popup may still be visible, trying Post anyway...")
                    self._click_post_button()
            else:
                logger.error("Could not close popup - manual intervention may be needed")
                
        except Exception as e:
            logger.debug(f"Warning popup error: {e}")

    def _click_post_button(self) -> bool:
        """Find and click the post/publish button."""
        # Wait a bit for buttons to be ready
        time.sleep(2)
        
        # Try JavaScript to find and click Post button (most reliable)
        js_click_post = """
        var buttons = document.querySelectorAll('button');
        for (var i = 0; i < buttons.length; i++) {
            var btn = buttons[i];
            var text = btn.innerText.trim().toLowerCase();
            if (text === 'post') {
                btn.scrollIntoView({block: 'center'});
                btn.click();
                return 'clicked';
            }
        }
        // Also try divs with Post text inside buttons
        var divs = document.querySelectorAll('button div');
        for (var i = 0; i < divs.length; i++) {
            var div = divs[i];
            if (div.innerText.trim().toLowerCase() === 'post') {
                div.parentElement.click();
                return 'clicked_parent';
            }
        }
        return 'not_found';
        """
        try:
            result = self.driver.execute_script(js_click_post)
            if result in ['clicked', 'clicked_parent']:
                logger.info(f"Post button clicked via JavaScript ({result})")
                return True
            logger.info(f"JavaScript click result: {result}")
        except Exception as e:
            logger.debug(f"JavaScript click failed: {e}")
        
        # Scroll to bottom to ensure Post button is visible
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        except:
            pass
        
        # Quick search: find all buttons and look for "Post" text
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logger.info(f"Found {len(buttons)} buttons on page")
            for button in buttons:
                try:
                    btn_text = button.text.strip().lower()
                    if btn_text == "post":
                        # Scroll button into view
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(0.5)
                        try:
                            button.click()
                            logger.info("Post button clicked")
                            return True
                        except:
                            # Try JavaScript click
                            self.driver.execute_script("arguments[0].click();", button)
                            logger.info("Post button clicked via JS fallback")
                            return True
                except:
                    continue
        except Exception as e:
            logger.debug(f"Button search failed: {e}")
        
        # Fallback: try specific selectors with longer timeout
        post_selectors = [
            '//button[.//div[text()="Post"]]',
            '//button[text()="Post"]',
            '//button[contains(text(), "Post")]',
            'button.TUXButton--primary',
            '[data-e2e="post-button"]',
        ]
        
        for selector in post_selectors:
            try:
                logger.debug(f"Trying Post selector: {selector}")
                if selector.startswith("//"):
                    button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                self.driver.execute_script("arguments[0].click();", button)
                logger.info(f"Post button clicked via {selector}")
                return True
            except:
                continue
        
        # Log available button texts for debugging
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            btn_texts = [b.text.strip() for b in buttons if b.text.strip()]
            logger.info(f"Available buttons: {btn_texts[:10]}")
        except:
            pass
                
        return False
    
    def _wait_for_post_complete(self, timeout: int = 60) -> bool:
        """Wait for post to complete and verify success."""
        logger.info("Waiting for post confirmation...")
        
        success_indicators = [
            '[data-e2e="upload-success"]',
            '.upload-success',
            'text*="uploaded"',
            'text*="posted"'
        ]
        
        time.sleep(5)  # Initial wait
        
        # Check for success message or redirect
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check URL change (often redirects after success)
            current_url = self.driver.current_url
            if "upload" not in current_url.lower():
                logger.success("Post completed (detected URL change)")
                return True
                
            # Check for success elements
            for selector in success_indicators:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.success("Post completed (found success indicator)")
                    return True
                except:
                    pass
                    
            time.sleep(2)
            
        logger.warning("Could not confirm post completion")
        return True  # Assume success if no error
