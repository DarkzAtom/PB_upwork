from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time 
from bs4 import BeautifulSoup
import logging

'''
This will probably be a choice to go. too much pain
in the ass with handling-> parsing every php request from network
'''



################# LOGGER ########################

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s',  # Log message format
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),  # Write logs to a file
        logging.StreamHandler()  # Print logs to the console
    ]
)

logger = logging.getLogger(__name__)

#################################################


def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()

        page = context.new_page()

        page.goto("https://www.rockauto.com/")

        time.sleep(5)

        content = page.content()
        print(content)
        
        with open('playwright_content_test.html', 'w', encoding='utf-8') as f:
            f.write(content)

        page.close()

        context.close()
        browser.close()


def click_elements_to_widen_tree():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()

        page = context.new_page()

        page.goto("https://www.rockauto.com/")

        time.sleep(2)

        logger.info("selecting elements to click")

        # elements_to_click = page.locator('div.ranavnode > a').all()

        # for i, element in enumerate(elements_to_click):
        #     i+=1
        #     try:
        #         if i<=1:
        #             continue
        #         logger.info(f"clicking element {i}")
        #         element.click(timeout=5000)
        #         time.sleep(1)
        #     except PlaywrightTimeoutError as e:
        #         logger.error(f"error clicking element {i}: {e}")

        elements_to_click = page.locator("div.ranavnode").all()

        elements_num = len(elements_to_click)

        time.sleep(5)

        logger.info(f"found {elements_num} elements to click")

        for i in range(elements_num + 2):
            try:
                if i < 2:
                    continue
                
                div_to_click = page.locator(f"div.ranavnode[id='nav[{i}]']")

                div_to_click.locator(f"td[id='navicon[{i}]'] > a").click(timeout=5000)
                logger.info(f"clicking element {i}")
                time.sleep(1)
            except PlaywrightTimeoutError as e:
                logger.error(f"error clicking element {i}: {e}")


        # page.locator("[id=\"navicon[9]\"] > a").click()
        # page.locator("[id=\"navicon[10]\"] > a").click()
        # page.locator("[id=\"navicon[11]\"] > a").click()
        # page.locator("[id=\"navicon[12]\"] > a").click()
        
        time.sleep(5)


        page.close()
        context.close()
        browser.close()



if __name__ == "__main__":
    click_elements_to_widen_tree()