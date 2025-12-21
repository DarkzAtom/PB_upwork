from anticaptchaofficial.imagecaptcha import *
import os
from dotenv import load_dotenv, find_dotenv
from utils import logger
import asyncio




async def extract_captcha(page):
    captcha_selector = 'img.captchaimage'
    captcha_element = page.locator(captcha_selector)

    # Check if it exists and is actually visible before proceeding
    if await captcha_element.count() > 0 and await captcha_element.is_visible():
        def _generate_id(length=8):
            import string, secrets
            alphabet = string.ascii_letters + string.digits
            return ''.join(secrets.choice(alphabet) for _ in range(length))

        captcha_image_id = _generate_id()
        # Ensure path exists (good practice)
        os.makedirs('scraper/captcha_images', exist_ok=True)
        
        file_path = f'scraper/captcha_images/{captcha_image_id}.png'
        await captcha_element.screenshot(path=file_path)
        
        return captcha_image_id
    
    return None # Return None explicitly if no captcha

    



#pip3 install anticaptchaofficial

async def solve_captcha(page, captcha_image_id):
    if not captcha_image_id:
        return None

    load_dotenv(find_dotenv())
    apikey_anticaptcha = os.getenv('APIKEY_ANTICAPTCHA')

    solver = imagecaptcha()
    solver.set_verbose(1)
    solver.set_key(apikey_anticaptcha)
    solver.set_soft_id(0)

    # Path must match what was saved in extract_captcha
    file_path = f'scraper/captcha_images/{captcha_image_id}.png'

    loop = asyncio.get_running_loop()
    
    # This runs the blocking network call in a thread pool
    captcha_text = await loop.run_in_executor(
        None,
        solver.solve_and_return_solution,
        file_path 
    )

    if captcha_text != 0:
        logger.info(f"Captcha solved: {captcha_text}")
        # Clean up the image file to save disk space
        if os.path.exists(file_path):
            os.remove(file_path)
        return captcha_text
    else:
        logger.error(f"Captcha failed: {solver.error_code}")
        return None


async def submit_result(page, solved_captcha_text):
    try:    
        text_field = page.locator('someelementtobefound')
        await text_field.press_sequentially(solved_captcha_text, delay=57)
        await text_field.press('Enter')
    except Exception as e:
        logger.info(f'Some error occured solving captcha: {e}')


async def handle_captcha_overlay(page):
    logger.warning("Captcha detected by background listener! Pausing scrape to solve...")
    
    # 1. Reuse your existing logic
    captcha_id = await extract_captcha(page)
    
    if captcha_id:
        text = await solve_captcha(page, captcha_id)
        if text:
            await submit_result(page, text)
            
            # CRITICAL: You must wait for the captcha to disappear 
            # so the main loop doesn't trigger this handler again immediately.
            await page.locator('img.captchaimage').wait_for(state="detached", timeout=15000)
            logger.info("Captcha solved and removed. Resuming scrape.")


async def main_captcha_flow(page):
    # 1. Try to get an ID
    captcha_id = await extract_captcha(page)
    
    # 2. Only solve if an ID was actually returned
    if captcha_id:
        captcha_text = await solve_captcha(page, captcha_image_id=captcha_id)
        
        # 3. Only submit if we got text back
        if captcha_text:
            await submit_result(page, captcha_text)
        else:
            logger.warning("Captcha image was found but could not be solved.")
    else:
        logger.info("No captcha detected on this page.")
