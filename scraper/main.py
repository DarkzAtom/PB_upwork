from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time 
from bs4 import BeautifulSoup
import logging
import random


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


def click_elements_by_car_brand():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()

        page = context.new_page()

        page.goto('https://www.rockauto.com/')

        time.sleep(1)

        logger.info('collecting info by car brand')


        brands_divs = page.locator('div.ranavnode').all()

        logger.info(f'total len of brands found: {len(brands_divs)}')

        brands = []


        #filtering out blank divs 
        for brand in brands_divs:
            brand_text = brand.locator('td.nlabel').text_content()
            if brand_text:
                brands.append(brand_text)



        # processing every brand separately

        brands_full_info: list = []
        brand_dict = {}

        for brand in brands:
            brand_dict
            logger.info(f'brand name: {brand}')
            # wide to see children (years)
            brand_td = page.locator('td.nlabel').get_by_text(brand, exact=True)
            brand_td.hover()
            brand_td.highlight()


            brand_td.click()
            time.sleep(random.uniform(0.1, 0.4))

            # processing years
            years = []

            logger.info('search years')

            brand_div = brand_td.locator('..').locator('..').locator('..').locator('..').locator('..').locator('..').locator('..')

            years_divs_group = brand_div.locator('div.nchildren')

            # years_divs_group = brand_div.locator('div.nchildren').first.wait_for(state='visible')

            logger.info('search 2')

            try:    
                years_divs = years_divs_group.locator('div.ranavnode').all()
            except Exception as e:
                logger.info(f'error {e}')

            logger.info(f'yearsdivs len: {len(years_divs)}')
            
            for year in years_divs:
                year_text = year.text_content()
                if year_text:
                    div_id = year.get_attribute('id')
                    year_dict = {
                        'year': year_text,
                        'div_id': div_id
                    }
                    years.append(year_dict)
                    logger.info(f'year: {year_text}, div_id: {div_id}')
                else:
                    logger.error('havent found anything')
                    continue

            for year in years:
                print(year)

            for year in years:    
                year_element = brand_div.get_by_text(year['year'])

                year_element.highlight()

                time.sleep(20)

                year_element.click()


                logger.info('clicked')

                time.sleep(2)


                # processing models
                models = []

                models_divs_group = page.locator(f"div[id='{year['div_id']}']").locator('div.nchildren')

                models_divs_group.highlight()

                time.sleep(35)




                


                
                


            
                


                

                

            time.sleep(3)
            




        time.sleep(30)








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
    click_elements_by_car_brand()