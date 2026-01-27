import os
import asyncio
import re
import pandas as pd
from datetime import datetime
from playwright import async_api
import zipfile
from openpyxl import load_workbook
import traceback
from pathlib import Path

class CanvasBot:
    """
    A class to automate interactions with Canvas, including login and navigation.
    """
    def __init__(self, email, password, canvas_url="https://canvas.uh.edu/"):
        """
        Initializes the CanvasBot with user credentials and the target URL.

        Args:
            email (str): The user's email address for login.
            password (str): The user's password for login.
            canvas_url (str): The base URL for the Canvas instance.
        """
        self.email = email
        self.password = password
        self.canvas_url = canvas_url
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def _initialize_browser(self):
        """Initializes the Playwright instance and launches a browser with anti-detection measures."""
        print("Initializing browser with anti-detection...")
        self.playwright = await async_api.async_playwright().start()
        
        self.browser = await self.playwright.firefox.launch(
            headless=False,
            firefox_user_prefs={
                "dom.webdriver.enabled": False,
                "useAutomationExtension": False,
                "general.platform.override": "MacIntel",
                "general.useragent.override": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
            }
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1440, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
            locale='en-US',
            timezone_id='America/Chicago',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        self.page = await self.context.new_page()
        
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        self.page.set_default_timeout(60000)
        print("Browser initialized successfully with anti-detection measures.")

    async def _close_browser(self):
        """Closes the browser and stops the Playwright instance."""
        if self.browser:
            await self.browser.close()
            print("Browser closed.")
        if self.playwright:
            await self.playwright.stop()

    async def _wait_for_navigation_complete(self, timeout=30000):
        """Waits for the page to fully load and become interactive."""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            await asyncio.sleep(0.5)
        except async_api.TimeoutError:
            print("Network idle timeout reached, falling back to 'domcontentloaded'.")
            await self.page.wait_for_load_state("domcontentloaded", timeout=timeout)

    async def navigate_to_content_uploader_and_upload(self, url):
        """Navigates to a specific URL and uploads all QTI files from the 'cias' directory."""
        print(f"\nNavigating to URL: {url}")
        await self.page.goto(url, wait_until="domcontentloaded")
        await self._wait_for_navigation_complete()
        
        cias_dir = Path("./cias")
        if not cias_dir.exists():
            print("❌ Error: ./cias directory not found!")
            return
            
        zip_files = list(cias_dir.glob("*.zip"))
        if not zip_files:
            print("❌ No zip files found in ./cias directory!")
            return
            
        print(f"Found {len(zip_files)} zip files to upload: {[f.name for f in zip_files]}")
        
        for zip_file in zip_files:
            await self._upload_single_qti_file(zip_file)
            await asyncio.sleep(3)

    async def _upload_single_qti_file(self, zip_file_path):
        """Uploads a single QTI zip file through the Canvas import flow."""
        file_name = zip_file_path.name
        file_name_without_ext = zip_file_path.stem
        
        print(f"\n📤 Starting upload for: {file_name}")
        
        try:
            # Step 1: Select QTI .zip file content type
            print("1. Selecting 'QTI .zip file' as the content type...")
            dropdown_opener = self.page.locator('[data-testid="select-content-type-dropdown"]')
            await dropdown_opener.wait_for(state="visible", timeout=15000)
            await dropdown_opener.click()
            print("Clicked the custom dropdown to open options.")
            
            await asyncio.sleep(1)
            
            qti_option = self.page.locator('div[role="option"]:has-text("QTI .zip file"), li:has-text("QTI .zip file")').first
            await qti_option.wait_for(state="visible", timeout=10000)
            await qti_option.click()
            print("✅ Successfully selected 'QTI .zip file'.")
            
            await asyncio.sleep(1)

            # Step 2: Upload the file using the direct input method
            print("2. Attaching the QTI .zip file...")
            file_input_locator = self.page.locator('input[type="file"]')
            await file_input_locator.set_input_files(str(zip_file_path))
            print(f"✅ File attached directly via set_input_files: {file_name}")

            await self.page.wait_for_selector(f'text="{file_name}"', timeout=10000)
            print("✅ Verified that the file name appeared on the page.")

            # Step 3: Select "Create new question bank" and name it
            print("3. Setting up new question bank...")
            new_bank_name_input = self.page.locator('input[placeholder="New question bank"]')

            if await new_bank_name_input.count() == 0:
                print("New bank name input not visible, clicking dropdown...")
                question_bank_dropdown = self.page.locator('[data-testid="questionBankSelect"]')
                await question_bank_dropdown.click()
                await asyncio.sleep(1)
                
                create_new_option = self.page.locator('div[role="option"]:has-text("Create new question bank"), li:has-text("Create new question bank")').first
                await create_new_option.click()
                print("✅ Selected 'Create new question bank'.")
                await asyncio.sleep(1)

            await new_bank_name_input.wait_for(state="visible", timeout=5000)
            await new_bank_name_input.fill(file_name_without_ext)
            print(f"✅ Set new question bank name to: {file_name_without_ext}")

            # Step 4: Handle additional options
            print("4. Checking additional options...")
            overwrite_checkbox = self.page.locator('input[type="checkbox"][name*="overwrite"]').first
            if await overwrite_checkbox.count() > 0:
                await overwrite_checkbox.check()
                print("✅ Enabled overwrite assessment content")
            
            # Step 5: Submit the form
            print("5. Submitting import...")
            # Use the stable data-testid from the provided HTML for the most reliable locator
            submit_button = self.page.locator('[data-testid="submitMigration"]')
            
            # Playwright's click action automatically waits for the element to be visible, stable, and enabled.
            await submit_button.click()
            print("✅ Clicked 'Add to Import Queue'.")
            
            await self._wait_for_navigation_complete()
            
            if "content_migrations" in self.page.url:
                print(f"✅ Successfully initiated import for: {file_name}")
            else:
                print(f"⚠️ Unexpected page after import: {self.page.url}")
                
        except Exception as e:
            print(f"❌ An unexpected error occurred during the upload of {file_name}:")
            traceback.print_exc()

    async def _handle_microsoft_login(self):
        """Handles the Microsoft/Azure AD login flow."""
        print("Handling Microsoft login...")
        try:
            email_input = self.page.locator('input[name="loginfmt"], input[type="email"]').first
            await email_input.wait_for(state="visible", timeout=10000)
            await email_input.fill(self.email)
            print("Filled email")

            next_button = self.page.locator('input[type="submit"][value="Next"], button:has-text("Next")').first
            async with self.page.expect_navigation(timeout=15000):
                await next_button.click()
            print("Clicked Next and navigated")
            await asyncio.sleep(1)

            password_input = self.page.locator('input[name="passwd"], input[type="password"]').first
            await password_input.wait_for(state="visible", timeout=15000)
            await password_input.fill(self.password)
            print("Filled password")

            sign_in_button = self.page.locator('input[type="submit"][value="Sign in"], button:has-text("Sign in")').first
            
            try:
                async with self.page.expect_navigation(timeout=10000):
                    await sign_in_button.click()
                print("Clicked Sign in and navigated")
            except:
                await sign_in_button.click()
                print("Clicked Sign in (no navigation)")
            
            await asyncio.sleep(2)

            try:
                if not self.page.is_closed():
                    stay_signed_in = self.page.locator('#idSIButton9, input[type="submit"][value="Yes"], button:has-text("Yes")').first
                    if await stay_signed_in.count() > 0:
                        try:
                            async with self.page.expect_navigation(timeout=10000):
                                await stay_signed_in.click()
                            print("Clicked 'Yes' for stay signed in and navigated")
                        except:
                            await stay_signed_in.click()
                            print("Clicked 'Yes' for stay signed in (no navigation)")
            except Exception as e:
                print(f"Stay signed in step failed or page navigated: {e}")

            await asyncio.sleep(2)

            try:
                if not self.page.is_closed():
                    duo_button = self.page.locator('button:has-text("Yes, this is my device"), .positive.auth-button, button:has-text("Trust this browser")').first
                    if await duo_button.count() > 0:
                        try:
                            async with self.page.expect_navigation(timeout=15000):
                                await duo_button.click()
                            print("Clicked MFA/Duo button and navigated")
                        except:
                            await duo_button.click()
                            print("Clicked MFA/Duo button (no navigation)")
            except Exception as e:
                print(f"MFA/Duo step failed or page navigated: {e}")
            
            return True

        except Exception as e:
            print(f"Error in Microsoft login flow: {e}")
            return True

    async def _login_to_canvas(self):
        """Navigates to Canvas and completes the login process."""
        print("Starting Canvas login process...")
        await self.page.goto(self.canvas_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        print(f"Navigated to Canvas, current URL: {self.page.url}")

        if "login.microsoftonline.com" in self.page.url:
            await self._handle_microsoft_login()

            print("Waiting for redirect back to Canvas...")
            try:
                await self.page.wait_for_url("**/canvas.uh.edu/**", timeout=60000)
                print("✅ Successfully redirected to Canvas!")
            except async_api.TimeoutError:
                print("URL timeout, checking for Canvas elements...")
                try:
                    await self.page.wait_for_selector('#global_nav_courses_link, .ic-app-header, #header', timeout=30000)
                    print("✅ Canvas elements detected!")
                except async_api.TimeoutError:
                    print(f"⚠️ Current URL after login attempt: {self.page.url}")
        
        await self._wait_for_navigation_complete()
        print(f"Canvas loaded! Current URL: {self.page.url}")
        
        try:
            await self.page.wait_for_selector('#global_nav_courses_link, .ic-app-header, #header', timeout=10000)
            print("✅ Login verification successful!")
        except:
            print("⚠️ Could not verify Canvas login, but proceeding...")

    async def run(self):
        """
        The main execution method to run the entire automation process.
        """
        try:
            await self._initialize_browser()
            await self._login_to_canvas()
            
            import_url = "https://canvas.uh.edu/courses/28570/content_migrations"
            await self.navigate_to_content_uploader_and_upload(import_url)

            print(f"\n--- Process Complete ---")
            print("✅ Bot finished uploading all QTI files.")

            print("\n🔍 Browser will stay open for 15 seconds for inspection...")
            await asyncio.sleep(15)

        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            if self.page and not self.page.is_closed():
                try:
                    screenshot_path = "error_screenshot.png"
                    await self.page.screenshot(path=screenshot_path, full_page=True)
                    print(f"Screenshot saved to {screenshot_path}")
                except:
                    print("Could not take screenshot (page may be closed)")
            print("Browser will stay open for 30 seconds for debugging...")
            await asyncio.sleep(30)
        
        finally:
            await self._close_browser()

# Example usage:
async def main():
    email = os.getenv("CANVAS_EMAIL", "EMAIL@CougarNet.UH.EDU")
    password = os.getenv("CANVAS_PASSWORD", "PASSWORD")
    
    if not email or "your_email" in email or not password or "your_password" in password:
        print("❌ Error: Please provide valid credentials in the script or set them as environment variables.")
        return

    bot = CanvasBot(email, password)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
