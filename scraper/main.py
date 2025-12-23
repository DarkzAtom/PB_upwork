from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import time 
from bs4 import BeautifulSoup
import logging
import random
import re
import asyncio
from captcha import captcha_monitor
from utils import logger



MAX_SCRAPED_PARTS = 0


class ScrapingLimitReached(Exception):
    pass


async def click_elements_by_car_brand():
    start_time = time.perf_counter()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False
            # args=[
            #     '--disable-blink-features=AutomationControlled',
            #     '--disable-dev-shm-usage',
            #     '--disable-gpu',
            #     '--no-sandbox'
            # ]
            )
        context = await browser.new_context( 
            # bypass_csp=True,    
            # java_script_enabled=True,  # Only if you need JS
        )

        page = await context.new_page()

        # await page.add_locator_handler(        commented out since redundant for now
        #     page.locator('img.captchaimage'),
        #     handle_captcha_overlay
        # )

        await page.goto('https://www.rockauto.com/en/catalog/')

        time.sleep(1)

        logger.info('collecting info by car brand')


        brands_divs = await page.locator('div.ranavnode').all()

        logger.info(f'total len of brands found: {len(brands_divs)}')

        brands = []


        #filtering out blank divs 
        for brand in brands_divs:
            brand_text = await brand.locator('td.nlabel').text_content()
            if brand_text:
                brands.append(brand_text)



        # processing every brand separately

        parts_final_list: list = []
        failed_years_processing: list = []
        
        try:
            for brand in brands:

                async def _get_years_by_brand(working_page, avoid_clicking=False):
                    logger.info(f'brand name: {brand}')

                    # Find the brand's div element - use .first to get only the top-level brand div
                    brand_div = working_page.locator(f'div.ranavnode:has(td.nlabel a:text-is("{brand}"))').first

                    if not avoid_clicking:
                        
                        # Click to expand brand (click the icon, not the label)
                        brand_icon_td = brand_div.locator('td.niconspace a').first
                        await brand_icon_td.click()

                        # Wait for direct children to load (use > to select only direct child)
                        await brand_div.locator('> div.nchildren').wait_for(state='visible', timeout=5000)

                    # processing years
                    
                    years = []
                    logger.info('search years')

                    years_divs_group = brand_div.locator('> div.nchildren').first
                    years_divs = await years_divs_group.locator('> div.ranavnode').all()

                    logger.info(f'yearsdivs len: {len(years_divs)}')

                    for year_div in years_divs:

                        # Get only the year label, not all nested content
                        year_label = year_div.locator('td.nlabel a').first
                        year_text = await year_label.text_content()

                        if year_text:
                            year_text = year_text.strip()
                            div_id = await year_div.get_attribute('id')
                            year_dict = {
                                'year': year_text,
                                'div_id': div_id
                            }
                            years.append(year_dict)
                            logger.info(f'year: {year_text}, div_id: {div_id}')
                        else:
                            logger.error('havent found anything')
                            continue
                        if years:
                            years_count = len(years)
                    return years, years_count
                
                _, years_count = await _get_years_by_brand(page)
                
                semaphore_years = asyncio.Semaphore(5)
                tasks_years = []


                async def _execute_year_in_tab(semaphore, year_idx):
                    async with semaphore:
                        try:
                            year = None  # init
                            monitor_task = None  # init
                            year_page = None  # init

                            year_page = await context.new_page()
                            monitor_task = asyncio.create_task(captcha_monitor(year_page))

                            # Helper function to click year
                            async def _click_year(page_to_click, year_to_click):
                                escaped_id = year_to_click['div_id'].replace('[', '\\[').replace(']', '\\]')
                                year_div = page_to_click.locator(f"div#{escaped_id}")
                                year_icon = year_div.locator('td.niconspace a').first
                                await year_icon.click()
                                logger.info(f'clicked year {year_to_click["year"]}')
                                return year_div
                            
                            # Get the list of models ONCE at the start
                            await year_page.goto('https://www.rockauto.com/en/catalog/')
                            years, _ = await _get_years_by_brand(year_page, avoid_clicking=False)
                            year = years[year_idx]
                            year_div = await _click_year(year_page, year)
                            await year_div.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                            
                            models_divs_group = year_div.locator('> div.nchildren').first
                            models_divs = await models_divs_group.locator('> div.ranavnode').all()
                            
                            # Extract model info (so we have it even after refresh)
                            models = []
                            for model_div in models_divs:
                                model_text = await model_div.locator('td.nlabel a').first.text_content()
                                model_div_id = await model_div.get_attribute('id')
                                models.append({'model': model_text.strip(), 'model_div_id': model_div_id})
                            
                            models_count = len(models)
                            logger.info(f"Found {models_count} models for year {year['year']}")
                            
                            # Loop through each model (NO refresh here)
                            for model_idx in range(models_count):
                                logger.info(f"Processing model {model_idx + 1}/{models_count}: {models[model_idx]['model']}")
                                
                                # Click to expand model
                                escaped_model_id = models[model_idx]['model_div_id'].replace('[', '\\[').replace(']', '\\]')
                                model_div_element = year_page.locator(f"div#{escaped_model_id}")
                                model_icon = model_div_element.locator('td.niconspace a').first
                                
                                if models_count > 1:
                                    await model_icon.click()

                                # Wait for submodels to load
                                try:
                                    await model_div_element.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                                except PlaywrightTimeoutError:
                                    logger.warning(f'No submodels found for {models[model_idx]["model"]}')
                                    continue

                                # Extract submodels info ONCE (so we have it even after refresh)
                                submodels = []
                                logger.info('processing submodels')
                                submodels_group_div = model_div_element.locator('> div.nchildren').first
                                submodel_divs = await submodels_group_div.locator('> div.ranavnode').all()
                                logger.info(f'found {len(submodel_divs)} submodels')

                                for submodel_div in submodel_divs:
                                    submodel_label = submodel_div.locator('td.nlabel a').first
                                    submodel_text = await submodel_label.text_content()

                                    if submodel_text:
                                        submodel_text = submodel_text.strip()
                                        submodel_div_id = await submodel_div.get_attribute('id')
                                        logger.info(f'found submodel: {submodel_text}, id: {submodel_div_id}')
                                        submodel_dict = {
                                            'submodel': submodel_text,
                                            'submodel_div_id': submodel_div_id
                                        }
                                        submodels.append(submodel_dict)
                                    else:
                                        logger.error('no text found for submodel')
                                        continue

                                submodels_count = len(submodels)

                                # NOW loop through each submodel with refresh between
                                for submodel_idx in range(submodels_count):
                                    submodel = submodels[submodel_idx]
                                    logger.info(f'Processing submodel {submodel_idx + 1}/{submodels_count}: {submodel["submodel"]}')

                                    # REFRESH and re-navigate to this specific submodel
                                    await year_page.goto('https://www.rockauto.com/en/catalog/')
                                    
                                    # Re-expand brand
                                    years, _ = await _get_years_by_brand(year_page, avoid_clicking=False)
                                    year = years[year_idx]
                                    
                                    # Re-expand year
                                    year_div = await _click_year(year_page, year)
                                    await year_div.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                                    
                                    # Re-expand the SPECIFIC model we're working on
                                    models_divs_group = year_div.locator('> div.nchildren').first
                                    fresh_models_divs = await models_divs_group.locator('> div.ranavnode').all()
                                    fresh_models_count = len(fresh_models_divs)
                                    
                                    #  Get the specific model by index
                                    fresh_model_div = fresh_models_divs[model_idx]
                                    
                                    fresh_model_icon = fresh_model_div.locator('td.niconspace a').first
                                    
                                    if fresh_models_count > 1:
                                        await fresh_model_icon.click()
                                    
                                    #  Wait for submodels to appear
                                    await fresh_model_div.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                                    
                                    # Get fresh submodels from the fresh model
                                    fresh_submodels_group = fresh_model_div.locator('> div.nchildren').first
                                    fresh_submodel_divs = await fresh_submodels_group.locator('> div.ranavnode').all()

                                    # Get the specific submodel by index
                                    fresh_submodel_div = fresh_submodel_divs[submodel_idx]
                                    submodel_icon = fresh_submodel_div.locator('td.niconspace a').first

                                    if submodels_count > 1:
                                        await submodel_icon.click()

                                    # Use fresh_submodel_div for the rest
                                    submodel_div_element = fresh_submodel_div
                                    
                                    # ... rest of the code

                                    # Wait for parts categories to load
                                    try:
                                        await submodel_div_element.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                                        logger.info(f'Parts loaded for {submodel["submodel"]}')
                                    except PlaywrightTimeoutError:
                                        logger.warning(f'No parts found for {submodel["submodel"]}')
                                        continue

                                    ######## category processing (rest of your code stays the same)
                                    categories = []
                                    category_group_div = submodel_div_element.locator('> div.nchildren').first
                                    category_divs = await category_group_div.locator('> div.ranavnode').all()

                                    for category_div in category_divs:
                                        category_label = category_div.locator('td.nlabel a').first
                                        category_text = await category_label.text_content()

                                        if category_text and not category_text=='Show Closeouts Only':
                                            category_text = category_text.strip()
                                            category_div_id = await category_div.get_attribute('id')
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
                                        category_div_element = year_page.locator(f'div#{escaped_category_id}')
                                        category_icon = category_div_element.locator('td.niconspace a').first

                                        if len(categories) > 1:
                                            logger.info(f"actually clicking for a category icon of {category['category']} of category div element {category['category_div_id']}")
                                            await category_icon.click()

                                        try:
                                            await category_div_element.locator('> div.nchildren').wait_for(state='visible', timeout=5000)
                                            logger.info(f'Parts loaded for {category["category"]}')
                                        except PlaywrightTimeoutError:
                                            logger.warning(f'No parts found for {category["category"]}')
                                            continue

                                        ######## subcategory part #######################
                                        subcategories = []
                                        subcategories_group_divs = category_div_element.locator('> div.nchildren').first
                                        subcategory_divs = await subcategories_group_divs.locator('> div.ranavnode').all()

                                        for subcategory_div in subcategory_divs:
                                            subcategory_label = subcategory_div.locator('td.nlabel a').first
                                            subcategory_text = await subcategory_label.text_content()

                                            if subcategory_text:
                                                subcategory_text = subcategory_text.strip()
                                                subcategory_div_id = await subcategory_div.get_attribute('id')
                                                subcategory_dict = {
                                                    'subcategory': subcategory_text,
                                                    'subcategory_div_id': subcategory_div_id
                                                }
                                                subcategories.append(subcategory_dict)
                                            else:
                                                logger.info('cant find a text in the subcategory element')
                                                continue

                                        for subcategory in subcategories:
                                            logger.info(f'scraped parts so far: {len(parts_final_list)}')
                                            logger.info(f"working with subcategory {subcategory['subcategory']} with div id {subcategory['subcategory_div_id']}")

                                            escaped_subcategory_id = subcategory['subcategory_div_id'].replace('[', '\\[').replace(']', '\\]')
                                            subcategory_div_element = year_page.locator(f'div#{escaped_subcategory_id}')
                                            subcategory_icon = subcategory_div_element.locator('td.niconspace a').first

                                            if len(subcategories) > 1:
                                                logger.info('actually clicking subcategory')
                                                await subcategory_icon.click()

                                            try:
                                                await subcategory_div_element.locator("> div.nchildren").wait_for(state='visible', timeout=5000)
                                                logger.info(f'Parts loaded for {category["category"]}')
                                            except PlaywrightTimeoutError:
                                                logger.warning(f"No success loading children of the subcategory element {subcategory['subcategory']} by id {subcategory['subcategory_div_id']}")
                                                continue

                                            ######## parts processing #######################
                                            parts = []
                                            parts_group_div = subcategory_div_element.locator('> div.nchildren').first.locator('> div.listings-container').first.locator('> form').first.locator('> div.listing-container-border').locator('> div').first.locator('> table').first
                                            if not parts_group_div:
                                                logger.info(f'No parts group found for subcategory {subcategory["subcategory"]}')
                                                continue

                                            part_html_content = await parts_group_div.inner_html()
                                            soup = BeautifulSoup(part_html_content, 'html.parser')

                                            part_divs = soup.find_all('tbody', class_='listing-inner', recursive=False)
                                            logger.info(f'found {len(part_divs)} parts in subcategory {subcategory["subcategory"]}')
                                            
                                            for part_div in part_divs:
                                                part_label = part_div.select_one('span.listing-final-manufacturer')
                                                part_text = part_label.get_text(strip=True) if part_label else None
                                                if part_text:
                                                    logger.info(f'successfully found the name of the manufacturer of the part {part_text}')
                                                    part_div_id = part_div.get('id')
                                                    part_dict = {
                                                        'part': part_text,
                                                        'part_div_id': part_div_id
                                                    }
                                                    parts.append(part_dict)
                                                else:
                                                    logger.info('cant find a text in the part element')
                                                    continue

                                            for part in parts:
                                                if len(parts_final_list) > MAX_SCRAPED_PARTS and MAX_SCRAPED_PARTS > 0:
                                                    logger.info(f'reached {MAX_SCRAPED_PARTS} parts, stopping the scraping')
                                                    raise ScrapingLimitReached()
                                                
                                                logger.info(f"working with part {part['part']} with div id {part['part_div_id']}")
                                                part_div_element = soup.find('tbody', id=part['part_div_id'])

                                                part_number = part_div_element.find('span', class_='listing-final-partnumber').get_text(strip=True) if part_div_element.find('span', class_='listing-final-partnumber') else None
                                                logger.info(f'current part number: {part_number}')

                                                manufacturer = part_div_element.find('span', class_='listing-final-manufacturer').get_text(strip=True) if part_div_element.find('span', class_='listing-final-manufacturer') else None
                                                logger.info(f'current manufacturer: {manufacturer}')
                                                
                                                images_link = part_div_element.find('img', class_='listing-inline-image')['src'] if part_div_element.find('img', class_='listing-inline-image') else None
                                                logger.info(f'current image link: {images_link}')
                                                
                                                name = part_div_element.find('span', class_='span-link-underline-remover').get_text(strip=True) if part_div_element.find('span', class_='span-link-underline-remover') else None
                                                logger.info(f'current part name: {name}')

                                                text = part_div_element.find('span', class_='listing-total').get_text(strip=True) if part_div_element.find('span', class_='listing-total') else None
                                                matches = re.findall(r'\d+\.?\d*', text) if text else []
                                                if matches:
                                                    base_price = matches[0]
                                                elif text is None:
                                                    base_price = None
                                                else:   
                                                    base_price = text
                                                
                                                if base_price == 'Out of Stock':
                                                    stock_status = False
                                                else:
                                                    stock_status = True
                                                
                                                currency = part_div_element.find('span', class_='listing-total').get_text(strip=True).split(r'+d')[0] if part_div_element.find('span', class_='listing-total') else None
                                                if not currency:
                                                    currency = None

                                                pack_size = part_div_element.find('span', class_='pack_size_box').get_text(strip=True) if part_div_element.find('span', class_='pack_size_box') else None

                                                if stock_status:
                                                    available_quantity = 'tobescraped'
                                                
                                                attributes = 'to be scraped'
                                                description = 'to be scraped'
                                                supplier_sku = 'to be determined later with the client' 
                                                info_link = part_div_element.find('a', class_='ra-btn-moreinfo').get('href') if part_div_element.find('a', class_='ra-btn-moreinfo') else None

                                                part_dict = {
                                                    'part_number': part_number,
                                                    'manufacturer': manufacturer,
                                                    'category': category['category'],
                                                    'subcategory': subcategory['subcategory'],
                                                    'images_link': images_link,
                                                    'attributes': attributes if attributes else None,
                                                    'car_manufacturer': brand,
                                                    'car_year': year['year'],
                                                    'car_model': models[model_idx]['model'],
                                                    'car_submodel': submodel['submodel'],
                                                    'name': name if name else None,
                                                    'description': description if description else None,
                                                    'base_price': base_price,
                                                    'currency': currency,
                                                    'available_quantity': available_quantity,
                                                    'stock_status': stock_status,
                                                    'supplier_sku': supplier_sku if supplier_sku else None,
                                                    'pack_size': pack_size,
                                                    'info_link': info_link
                                                }

                                                logger.info('final dict of a part')
                                                logger.info('###################\n################\n###############')

                                                for key, value in part_dict.items():
                                                    logger.info(f'{key}: {value}')

                                                parts_final_list.append(part_dict)
                                                logger.info('added part info to final parts list')

                            
                        except Exception as e:
                            year_display = year if year else f'year_idx_{year_idx} (year is inaccessible)'
                            logger.warning(f'execution of the year {year_display} of brand {brand} has failed')
                            failed_dict = {
                                'year': year_display,
                                'brand': brand
                            }
                            failed_years_processing.append(failed_dict)
                        finally:
                            if 'monitor_task' in locals():
                                monitor_task.cancel()
                            await year_page.close()

                for year_idx in range(years_count):
                    
                    tasks_years.append(_execute_year_in_tab(semaphore_years, year_idx))
                results = await asyncio.gather(*tasks_years)
                print("years are sent to parallel execution successfully!")
        except ScrapingLimitReached:
            logger.info('scraping limit reached, stopping the process')
        except Exception as e:
            logger.error(f'Unexpected error occurred: {e.__traceback__.tb_lineno} - {str(e)}')
        finally:
            logger.info(f'total number of scraped parts (unsaved due to the crash) {len(parts_final_list)}')                            

        await context.close()
        await browser.close()

        '''save to the csv the final list'''

        save_to_csv(parts_final_list, 'scraper/rockauto_parts.csv')
        
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
    asyncio.run(click_elements_by_car_brand())