from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time 
from bs4 import BeautifulSoup
import logging
import random
import re


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


class ScrapingLimitReached(Exception):
    pass


def click_elements_by_car_brand():
    start_time = time.perf_counter()
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

        parts_final_list: list = []
        
        try:
            for brand in brands:
                logger.info(f'brand name: {brand}')

                # Find the brand's div element - use .first to get only the top-level brand div
                brand_div = page.locator(f'div.ranavnode:has(td.nlabel a:text-is("{brand}"))').first

                # Click to expand brand (click the icon, not the label)
                brand_icon_td = brand_div.locator('td.niconspace a').first
                brand_icon_td.click()

                # Wait for direct children to load (use > to select only direct child)
                brand_div.locator('> div.nchildren').wait_for(state='visible', timeout=5000)

                # processing years
                def _get_years():
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
                    return years
                years = _get_years()

                for year in years:
                    print(year)

                for year in years:
                    # Use the specific div ID to locate and click
                    # Escape the brackets in the ID for CSS selector
                    escaped_id = year['div_id'].replace('[', '\\[').replace(']', '\\]')
                    year_div = page.locator(f"div#{escaped_id}")
                    year_icon = year_div.locator('td.niconspace a').first

                    year_icon.highlight()


                    if len(years) > 1:
                        year_icon.click()


                    logger.info('clicked year')

                    # Wait for models to load
                    year_div.locator('> div.nchildren').wait_for(state='visible', timeout=5000)

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

                        if len(models) > 1:
                            model_icon.click()

                        # Wait for submodels to load
                        try:
                            model_div_element.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
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
                            if len(submodels) > 1:
                                submodel_icon.click()

                            # Wait for parts categories to load
                            try:
                                submodel_div_element.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                                logger.info(f'Parts loaded for {submodel["submodel"]}')
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

                                if len(categories) > 1:
                                    logger.info(f"actually clicking for a category icon of {category['category']} of category div element {category['category_div_id']}")
                                    category_icon.click()

                                # Wait for parts subcategories to load
                                try:
                                    category_div_element.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                                    logger.info(f'Parts loaded for {category["category"]}')
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

                                    if len(subcategories) > 1:
                                        logger.info('actually clicking subcategory')
                                        subcategory_icon.click()

                                    try:
                                        subcategory_div_element.locator("> div.nchildren").wait_for(state='visible', timeout=5000)
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

                                        # if len(parts_final_list) > 100:
                                        #     logger.info('reached 100 parts, stopping the scraping')
                                        #     raise ScrapingLimitReached() 

                                        logger.info(f"working with part {part['part']} with div id {part['part_div_id']}")
                                        escaped_part_id = part['part_div_id'].replace('[', '\\[').replace(']', '\\]')
                                        part_div_element = page.locator(f'tbody#{escaped_part_id}').first
                                        part_div_element.highlight()

                                        
                                        part_number  = part_div_element.locator('span.listing-final-partnumber').first.text_content().strip()
                                        logger.info(f'current part number: {part_number}')

                                        manufacturer = part_div_element.locator('span.listing-final-manufacturer').first.text_content().strip()
                                        logger.info(f'current manufacturer: {manufacturer}')

                                        if part_div_element.locator('img.listing-inline-image').count() > 0:
                                            images_link  = part_div_element.locator('img.listing-inline-image').first.get_attribute('src')
                                        else:
                                            images_link = None
                                        logger.info(f'current image link: {images_link}')

                                        if part_div_element.locator('span.span-link-underline-remover').count() > 0:
                                            name = part_div_element.locator('span.span-link-underline-remover').first.text_content().strip()
                                        else:
                                            name = None
                                        logger.info(f'current part name: {name}')
                                        
                                        
                                        if part_div_element.locator('span.listing-total').count() > 0:
                                            text = part_div_element.locator('span.listing-total').first.text_content().strip()
                                            matches = re.findall(r'\d+\.?\d*', text)
                                            if matches:
                                                base_price = matches[0]
                                            else:   
                                                base_price = text
                                        else:
                                            base_price = None
                                        if base_price == 'Out of Stock':
                                            stock_status = False
                                        else:
                                            stock_status = True
                                        currency = part_div_element.locator('span.listing-total').first.text_content().strip().split(r'+d')[0]
                                        if not currency:
                                            currency = None


                                        if part_div_element.locator('span.pack_size_box').count() > 0:
                                            pack_size = part_div_element.locator('span.pack_size_box').first.text_content().strip()
                                        else:
                                            pack_size = None
                                        


                                        # description and attributes fetching section 

                                        # logger.info('checking for more info link for the part to extract description and attributes')

                                        # if part_div_element.locator('a.ra-btn-moreinfo').count() > 0:    
                                        #     info_btn = part_div_element.locator('a.ra-btn-moreinfo').first
                                        #     # logger.info(f'info link: {info_link}')
                                        #     # info_btn.click()
                                        #     # time.sleep(10)
                                        #     # all_pages = page.context.pages
                                        #     # html_content = all_pages[1].content()
                                        #     # all_pages[1].close()  # close the new tab after parsing all the data
                                        #     with context.expect_page() as new_page_info:
                                        #         info_btn.click()
                                        #     new_page = new_page_info.value

                                        #     new_page.wait_for_load_state(state='domcontentloaded')

                                        #     new_page_html_content = new_page.content()

                                        #     new_page.close()

                                        #     attributes, description = extract_description_and_attributes(new_page_html_content)
                                            
                                        # else:
                                        #     attributes = None
                                        #     description = None
                                        #     logger.info('no info link found for the part, skipping description and attributes')
                                        
                                        if stock_status:
                                            available_quantity = 'tobescraped' # will be handled with separate logic but for it i need to add every single thing into the cart
                                        
                                        attributes = 'to be scraped'
                                        description = 'to be scraped'

                                        supplier_sku = 'to be determined later with the client' 

                                        part_dict = {
                                            'part_number': part_number,
                                            'manufacturer': manufacturer,
                                            'category': category['category'],
                                            'subcategory': subcategory['subcategory'],
                                            'images_link': images_link,
                                            'attributes': attributes if attributes else None,
                                            'car_manufacturer': brand,
                                            'car_year': year['year'],
                                            'car_model': model['model'],
                                            'car_submodel': submodel['submodel'],
                                            'name': name if name else None,
                                            'description': description if description else None,
                                            'base_price': base_price,
                                            'currency': currency,
                                            'available_quantity': available_quantity,
                                            'stock_status': stock_status,
                                            'supplier_sku': supplier_sku if supplier_sku else None,
                                            'pack_size': pack_size
                                        }

                                        for key, value in part_dict.items():
                                            logger.info(f'{key}: {value}')

                                        parts_final_list.append(part_dict)

                                        logger.info('added part info to final parts list')




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
                page.goto('https://www.rockauto.com/')
        except ScrapingLimitReached:
            logger.info('scraping limit reached, stopping the process')
        except Exception as e:
            logger.error(f'Unexpected error occurred: {e.__traceback__.tb_lineno} - {str(e)}')                            

        context.close()
        browser.close()

        '''save to the csv the final list'''

        save_to_csv(parts_final_list, 'rockauto_parts.csv')
        
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    logger.info(f'Scraping completed in {elapsed_time:.2f} seconds')
                    

def save_to_csv(parts_list: list, filename: str):
    import csv

    if not parts_list:
        logger.info('No parts to save.')
        return

    keys = parts_list[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(parts_list)


def extract_description_and_attributes(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    description_div = soup.find('section', {'aria-label': lambda x: x and x.startswith('More Information for')})

    if description_div:
        description_text = description_div.find(text=True, recursive=False)
        description = description_text.strip() if description_text else 'No description text found'
        logger.info(f'Description text from BeautifulSoup: {description_text}')
    else:
        logger.error('Description div not found using BeautifulSoup')
        description = None

    attributes_div = soup.find('section', {'aria-label': lambda x: x and 'Specifications' in x})
    if attributes_div:
        attributes = {}
        attr_table = attributes_div.select_one('table > tbody')
        attr_rows = attr_table.find_all('tr') if attr_table else []
        for row in attr_rows:
            cols = row.find_all('td')
            if len(cols) == 2:
                attr_name = cols[0].get_text(strip=True)
                attr_value = cols[1].get_text(strip=True)
                logger.info(f'Attribute: {attr_name} => Value: {attr_value}')
                attributes[attr_name] = attr_value
    else:
        logger.error('Attributes div not found using BeautifulSoup')
        attributes = None

    return attributes, description



if __name__ == "__main__":
    click_elements_by_car_brand()