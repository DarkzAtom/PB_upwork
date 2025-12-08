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
            logger.info(f'brand name: {brand}')

            # Find the brand's div element - use .first to get only the top-level brand div
            brand_div = page.locator(f'div.ranavnode:has(td.nlabel a:text-is("{brand}"))').first

            # Click to expand brand (click the icon, not the label)
            brand_icon_td = brand_div.locator('td.niconspace a').first
            brand_icon_td.click()

            # Wait for direct children to load (use > to select only direct child)
            brand_div.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
            time.sleep(random.uniform(0.1, 0.4))

            # processing years
            years = []
            logger.info('search years')

            years_divs_group = brand_div.locator('> div.nchildren').first
            years_divs = years_divs_group.locator('> div.ranavnode').all()

            logger.info(f'yearsdivs len: {len(years_divs)}')

            for year_div in years_divs:
                # Get only the year label, not all nested content
                year_label = year_div.locator('td.nlabel a').first
                year_text = year_label.text_content().strip()

                if year_text:
                    div_id = year_div.get_attribute('id')
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
                # Use the specific div ID to locate and click
                # Escape the brackets in the ID for CSS selector
                escaped_id = year['div_id'].replace('[', '\\[').replace(']', '\\]')
                year_div = page.locator(f"div#{escaped_id}")
                year_icon = year_div.locator('td.niconspace a').first

                year_icon.highlight()
                time.sleep(1)


                if len(years) > 1:
                    year_icon.click()


                logger.info('clicked year')

                # Wait for models to load
                year_div.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                time.sleep(random.uniform(0.2, 0.5))

                # processing models
                models = []

                models_divs_group = year_div.locator('> div.nchildren').first
                models_divs = models_divs_group.locator('> div.ranavnode').all()

                logger.info(f'found {len(models_divs)} models')

                for model_div in models_divs:
                    # Get only the model label text
                    model_label = model_div.locator('td.nlabel a').first
                    model_text = model_label.text_content().strip()

                    if model_text:
                        model_div_id = model_div.get_attribute('id')
                        model_dict = {
                            'model': model_text,
                            'model_div_id': model_div_id
                        }
                        models.append(model_dict)
                        logger.info(f"added model: {model_dict['model']}, id: {model_div_id}")
                    else:
                        logger.error('havent found anything in models')
                        continue

                for model in models:
                    logger.info(f"processing model: {model['model']}")

                    # Click the model icon to expand
                    # Escape the brackets in the ID for CSS selector
                    escaped_model_id = model['model_div_id'].replace('[', '\\[').replace(']', '\\]')
                    model_div_element = page.locator(f"div#{escaped_model_id}")
                    model_icon = model_div_element.locator('td.niconspace a').first

                    model_icon.highlight()
                    time.sleep(1)

                    if len(models) > 1:
                        model_icon.click()

                    # Wait for submodels to load
                    try:
                        model_div_element.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                        time.sleep(random.uniform(0.2, 0.5))
                    except PlaywrightTimeoutError:
                        logger.warning(f'No submodels found for {model["model"]}')
                        continue



                    # processing submodels (engine configurations)
                    submodels = []

                    logger.info('processing submodels')

                    submodels_group_div = model_div_element.locator('> div.nchildren').first
                    submodel_divs = submodels_group_div.locator('> div.ranavnode').all()

                    logger.info(f'found {len(submodel_divs)} submodels')

                    for submodel_div in submodel_divs:
                        # Get only the submodel label text
                        submodel_label = submodel_div.locator('td.nlabel a').first
                        submodel_text = submodel_label.text_content().strip()

                        if submodel_text:
                            submodel_div_id = submodel_div.get_attribute('id')
                            logger.info(f'found submodel: {submodel_text}, id: {submodel_div_id}')
                            submodel_dict = {
                                'submodel': submodel_text,
                                'submodel_div_id': submodel_div_id
                            }
                            submodels.append(submodel_dict)
                        else:
                            logger.error('no text found for submodel')
                            continue

                    for submodel in submodels:
                        logger.info(f'clicking submodel: {submodel["submodel"]}')

                        # Click the submodel icon to expand parts
                        # Escape the brackets in the ID for CSS selector
                        escaped_submodel_id = submodel['submodel_div_id'].replace('[', '\\[').replace(']', '\\]')
                        submodel_div_element = page.locator(f"div#{escaped_submodel_id}")
                        submodel_icon = submodel_div_element.locator('td.niconspace a').first

                        submodel_icon.highlight()
                        time.sleep(1)
                        if len(submodels) > 1:
                            submodel_icon.click()

                        # Wait for parts categories to load
                        try:
                            submodel_div_element.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                            time.sleep(random.uniform(0.2, 0.5))
                            logger.info(f'Parts loaded for {submodel["submodel"]}')

                            # Here you can collect part categories if needed
                            # part_categories = submodel_div_element.locator('> div.nchildren > div.ranavnode').all()
                            # ... process part categories ...

                        except PlaywrightTimeoutError:
                            logger.warning(f'No parts found for {submodel["submodel"]}')


                        

                        ######## category processing

                        categories = []

                        category_group_div = submodel_div_element.locator('> div.nchildren').first
                        category_divs = category_group_div.locator('> div.ranavnode').all()

                        for category_div in category_divs:
                            #extracting the text from the div
                            category_label = category_div.locator('td.nlabel a').first
                            category_text = category_label.text_content().strip()

                            if category_text and not category_text=='Show Closeouts Only':
                                category_div_id = category_div.get_attribute('id')
                                category_dict = {
                                    'category': category_text,
                                    "category_div_id": category_div_id
                                }
                                categories.append(category_dict)
                            else:
                                logger.info("Can't find category text")
                                continue

                        for category in categories:
                            logger.info(f"locating and clicking category {category['category']} with the id of {category['category_div_id']}")

                            escaped_category_id = category['category_div_id'].replace('[', '\\[').replace(']', '\\]')

                            category_div_element = page.locator(f'div#{escaped_category_id}')

                            category_icon = category_div_element.locator('td.niconspace a').first

                            category_icon.highlight()

                            time.sleep(1)
                            if len(categories) > 1:
                                logger.info(f"actually clicking for a category icon of {category['category']} of category div element {category['category_div_id']}")
                                category_icon.click()

                            # Wait for parts subcategories to load
                            try:
                                category_div_element.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                                time.sleep(random.uniform(0.2, 0.5))
                                logger.info(f'Parts loaded for {category["category"]}')

                                # Here you can collect part sub if needed
                                # part_categories = submodel_div_element.locator('> div.nchildren > div.ranavnode').all()
                                # ... process part categories ...

                            except PlaywrightTimeoutError:
                                logger.warning(f'No parts found for {category["category"]}')


                            
                            ######## subcategory part #######################

                            subcategories = []

                            subcategories_group_divs = category_div_element.locator('> div.nchildren').first
                            subcategory_divs = subcategories_group_divs.locator('> div.ranavnode').all()

                            for subcategory_div in subcategory_divs:
                                subcategory_label = subcategory_div.locator('td.nlabel a').first
                                subcategory_text = subcategory_label.text_content().strip()

                                if subcategory_text:

                                    subcategory_div_id = subcategory_div.get_attribute('id')
                                    subcategory_dict = {
                                        'subcategory': subcategory_text,
                                        'subcategory_div_id': subcategory_div_id
                                    }
                                    subcategories.append(subcategory_dict)
                                else:
                                    logger.info('cant find a text in the subcategory element')
                                    continue

                            for subcategory in subcategories:
                                logger.info(f"working with subcategory {subcategory['subcategory']} with div id {subcategory['subcategory_div_id']}")

                                escaped_subcategory_id = subcategory['subcategory_div_id'].replace('[', '\\[').replace(']', '\\]')
                                subcategory_div_element = page.locator(f'div#{escaped_subcategory_id}')
                                subcategory_icon = subcategory_div_element.locator('td.niconspace a').first

                                subcategory_icon.highlight()

                                time.sleep(1)

                                if len(subcategories) > 1:
                                    logger.info('actually clicking subcategory')
                                    subcategory_icon.click()

                                try:
                                    subcategory_div_element.locator("> div.nchildren").wait_for(state='visible', timeout=5000)
                                    time.sleep(random.uniform(0.2, 0.5))
                                    logger.info(f'Parts loaded for {category["category"]}')
                                except PlaywrightTimeoutError:
                                    logger.warning(f"No success loading children of the subcategory element {subcategory['subcategory']} by id {subcategory['subcategory_div_id']}")


                                ######## parts processing #######################


                                parts = []
                                parts_group_div = subcategory_div_element.locator('> div.nchildren').first.locator('> div.listings-container').first.locator('> form').first.locator('> div.listing-container-border').locator('> div').first.locator('> table').first
                                if not parts_group_div:
                                    logger.info(f'No parts group found for subcategory {subcategory["subcategory"]}')
                                    continue

                                

                                part_divs = parts_group_div.locator('> tbody.listing-inner').all()
                                logger.info(f'found {len(part_divs)} parts in subcategory {subcategory["subcategory"]}')
                                for part_div in part_divs:
                                    part_label = part_div.locator('span.listing-final-manufacturer').first
                                    part_text = part_label.text_content().strip()

                                    if part_text:
                                        logger.info(f'successfully found the name of the manufacturer of the part {part_text}')
                                        part_div_id = part_div.get_attribute('id')
                                        part_dict = {
                                            'part': part_text,
                                            'part_div_id': part_div_id
                                        }
                                        parts.append(part_dict)
                                    else:
                                        logger.info('cant find a text in the part element')
                                        continue

                                for part in parts:
                                    logger.info(f"working with part {part['part']} with div id {part['part_div_id']}")
                                    escaped_part_id = part['part_div_id'].replace('[', '\\[').replace(']', '\\]')
                                    part_div_element = page.locator(f'div#{escaped_part_id}')
                                    part_div_element.highlight()

                                

                                '''what is needed to be scraped from a part
                                1. part_id
                                2. supplier_part_id / catalog_id
                                3. brand_id
                                4. part_number
                                5. normalized_part_number
                                6. name 
                                7. description
                                8. category_id
                                9. subcategory_id
                                10. images
                                11. attributes
                                12. vehicle_fitment
                                '''
                                





                            


                time.sleep(1)




                


                
                


            
                


                

                

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