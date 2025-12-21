from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time 
from bs4 import BeautifulSoup
import logging
import re
import asyncio

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ScrapingLimitReached(Exception):
    pass


def click_elements_by_car_brand():
    """
    Optimized approach: Open everything quickly, then extract data efficiently
    Key optimizations:
    1. Click without waiting (fire and forget)
    2. Use JavaScript execution for faster clicking
    3. Disable unnecessary waiting
    4. Extract data in batches after expansion
    """
    start_time = time.perf_counter()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',  # Speed up by skipping some checks
                '--disable-features=IsolateOrigins,site-per-process',  # Reduce overhead
            ]
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # Block only heavy resources, keep minimal CSS for functionality
        page.route("**/*", lambda route: route.abort() 
                   if route.request.resource_type in ["image", "font", "media"] 
                   else route.continue_())
        
        page.goto('https://www.rockauto.com/')
        page.wait_for_load_state('networkidle')

        logger.info('Starting optimized breadth-first scraping')
        
        parts_final_list = []
        
        try:
            # LEVEL 1: Brands - Click all rapidly
            logger.info('=== LEVEL 1: Opening all brands ===')
            brands_data = collect_and_click_all_brands(page)
            logger.info(f'Opened {len(brands_data)} brands')
            
            # Wait for all brands' children to load
            wait_for_network_idle(page)
            
            # LEVEL 2: Years - Click all rapidly
            logger.info('=== LEVEL 2: Opening all years ===')
            years_data = collect_and_click_all_years(page, brands_data)
            logger.info(f'Opened {len(years_data)} years')
            wait_for_network_idle(page)
            
            # LEVEL 3: Models - Click all rapidly
            logger.info('=== LEVEL 3: Opening all models ===')
            models_data = collect_and_click_all_models(page, years_data)
            logger.info(f'Opened {len(models_data)} models')
            wait_for_network_idle(page)
            
            # LEVEL 4: Submodels - Click all rapidly
            logger.info('=== LEVEL 4: Opening all submodels ===')
            submodels_data = collect_and_click_all_submodels(page, models_data)
            logger.info(f'Opened {len(submodels_data)} submodels')
            wait_for_network_idle(page)
            
            # LEVEL 5: Categories - Click all rapidly
            logger.info('=== LEVEL 5: Opening all categories ===')
            categories_data = collect_and_click_all_categories(page, submodels_data)
            logger.info(f'Opened {len(categories_data)} categories')
            wait_for_network_idle(page)
            
            # LEVEL 6: Subcategories - Click all rapidly
            logger.info('=== LEVEL 6: Opening all subcategories ===')
            subcategories_data = collect_and_click_all_subcategories(page, categories_data)
            logger.info(f'Opened {len(subcategories_data)} subcategories')
            wait_for_network_idle(page)
            
            # LEVEL 7: Extract all parts
            logger.info('=== LEVEL 7: Extracting all parts ===')
            parts_final_list = extract_all_parts(page, context, subcategories_data)
            logger.info(f'Total parts extracted: {len(parts_final_list)}')
                
        except ScrapingLimitReached:
            logger.info('Scraping limit reached')
        except Exception as e:
            logger.error(f'Unexpected error: {e.__traceback__.tb_lineno} - {str(e)}')
        
        context.close()
        browser.close()
        
        save_to_csv(parts_final_list, 'rockauto_parts.csv')
        
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    logger.info(f'Scraping completed in {elapsed_time:.2f} seconds')


def wait_for_network_idle(page, timeout=30000):
    """Wait for network to be idle after bulk clicking"""
    try:
        page.wait_for_load_state('networkidle', timeout=timeout)
    except PlaywrightTimeoutError:
        logger.warning('Network idle timeout - continuing anyway')
        time.sleep(2)  # Give it a bit more time


def click_with_js(page, element):
    """Click using JavaScript for speed - bypasses Playwright's slow clicking"""
    try:
        page.evaluate('(element) => element.click()', element.element_handle())
    except Exception as e:
        logger.warning(f'JS click failed: {e}')


def collect_and_click_all_brands(page):
    """Collect all brands and click them all rapidly"""
    brands_data = []
    brands_divs = page.locator('div.ranavnode').all()
    
    # First pass: collect data
    for brand_div in brands_divs:
        brand_text = brand_div.locator('td.nlabel').text_content()
        if brand_text:
            brands_data.append({
                'brand': brand_text,
                'brand_div': brand_div
            })
    
    logger.info(f'Found {len(brands_data)} brands, clicking all...')
    
    # Second pass: click all rapidly without waiting
    click_count = 0
    for brand_item in brands_data:
        try:
            brand_icon = brand_item['brand_div'].locator('td.niconspace a').first
            click_with_js(page, brand_icon)
            click_count += 1
            if click_count % 10 == 0:
                logger.info(f'Clicked {click_count}/{len(brands_data)} brands')
        except Exception as e:
            logger.warning(f"Failed to click brand {brand_item['brand']}: {e}")
    
    return brands_data


def collect_and_click_all_years(page, brands_data):
    """Collect all years across all brands and click them rapidly"""
    years_data = []
    
    for brand_item in brands_data:
        brand_text = brand_item['brand']
        brand_div = page.locator(f'div.ranavnode:has(td.nlabel a:text-is("{brand_text}"))').first
        
        try:
            years_divs_group = brand_div.locator('> div.nchildren').first
            years_divs = years_divs_group.locator('> div.ranavnode').all()
            
            for year_div in years_divs:
                year_text = year_div.locator('td.nlabel a').first.text_content().strip()
                if year_text:
                    years_data.append({
                        'brand': brand_text,
                        'year': year_text,
                        'year_div': year_div
                    })
        except Exception as e:
            logger.warning(f'Error collecting years for {brand_text}: {e}')
    
    logger.info(f'Found {len(years_data)} years, clicking all...')
    
    # Click all years rapidly
    click_count = 0
    for year_item in years_data:
        try:
            year_icon = year_item['year_div'].locator('td.niconspace a').first
            click_with_js(page, year_icon)
            click_count += 1
            if click_count % 50 == 0:
                logger.info(f'Clicked {click_count}/{len(years_data)} years')
        except Exception as e:
            logger.warning(f"Failed to click year: {e}")
    
    return years_data


def collect_and_click_all_models(page, years_data):
    """Collect all models and click them rapidly"""
    models_data = []
    
    for year_item in years_data:
        try:
            year_div = year_item['year_div']
            models_divs_group = year_div.locator('> div.nchildren').first
            models_divs = models_divs_group.locator('> div.ranavnode').all()
            
            for model_div in models_divs:
                model_text = model_div.locator('td.nlabel a').first.text_content().strip()
                if model_text:
                    models_data.append({
                        'brand': year_item['brand'],
                        'year': year_item['year'],
                        'model': model_text,
                        'model_div': model_div
                    })
        except Exception as e:
            logger.warning(f"Error collecting models: {e}")
    
    logger.info(f'Found {len(models_data)} models, clicking all...')
    
    click_count = 0
    for model_item in models_data:
        try:
            model_icon = model_item['model_div'].locator('td.niconspace a').first
            click_with_js(page, model_icon)
            click_count += 1
            if click_count % 50 == 0:
                logger.info(f'Clicked {click_count}/{len(models_data)} models')
        except Exception as e:
            logger.warning(f"Failed to click model: {e}")
    
    return models_data


def collect_and_click_all_submodels(page, models_data):
    """Collect all submodels and click them rapidly"""
    submodels_data = []
    
    for model_item in models_data:
        try:
            model_div = model_item['model_div']
            submodels_group = model_div.locator('> div.nchildren').first
            submodel_divs = submodels_group.locator('> div.ranavnode').all()
            
            for submodel_div in submodel_divs:
                submodel_text = submodel_div.locator('td.nlabel a').first.text_content().strip()
                if submodel_text:
                    submodels_data.append({
                        'brand': model_item['brand'],
                        'year': model_item['year'],
                        'model': model_item['model'],
                        'submodel': submodel_text,
                        'submodel_div': submodel_div
                    })
        except Exception as e:
            logger.warning(f"Error collecting submodels: {e}")
    
    logger.info(f'Found {len(submodels_data)} submodels, clicking all...')
    
    click_count = 0
    for submodel_item in submodels_data:
        try:
            submodel_icon = submodel_item['submodel_div'].locator('td.niconspace a').first
            click_with_js(page, submodel_icon)
            click_count += 1
            if click_count % 50 == 0:
                logger.info(f'Clicked {click_count}/{len(submodels_data)} submodels')
        except Exception as e:
            logger.warning(f"Failed to click submodel: {e}")
    
    return submodels_data


def collect_and_click_all_categories(page, submodels_data):
    """Collect all categories and click them rapidly"""
    categories_data = []
    
    for submodel_item in submodels_data:
        try:
            submodel_div = submodel_item['submodel_div']
            category_group = submodel_div.locator('> div.nchildren').first
            category_divs = category_group.locator('> div.ranavnode').all()
            
            for category_div in category_divs:
                category_text = category_div.locator('td.nlabel a').first.text_content().strip()
                if category_text and category_text != 'Show Closeouts Only':
                    categories_data.append({
                        'brand': submodel_item['brand'],
                        'year': submodel_item['year'],
                        'model': submodel_item['model'],
                        'submodel': submodel_item['submodel'],
                        'category': category_text,
                        'category_div': category_div
                    })
        except Exception as e:
            logger.warning(f"Error collecting categories: {e}")
    
    logger.info(f'Found {len(categories_data)} categories, clicking all...')
    
    click_count = 0
    for category_item in categories_data:
        try:
            category_icon = category_item['category_div'].locator('td.niconspace a').first
            click_with_js(page, category_icon)
            click_count += 1
            if click_count % 50 == 0:
                logger.info(f'Clicked {click_count}/{len(categories_data)} categories')
        except Exception as e:
            logger.warning(f"Failed to click category: {e}")
    
    return categories_data


def collect_and_click_all_subcategories(page, categories_data):
    """Collect all subcategories and click them rapidly"""
    subcategories_data = []
    
    for category_item in categories_data:
        try:
            category_div = category_item['category_div']
            subcategories_group = category_div.locator('> div.nchildren').first
            subcategory_divs = subcategories_group.locator('> div.ranavnode').all()
            
            for subcategory_div in subcategory_divs:
                subcategory_text = subcategory_div.locator('td.nlabel a').first.text_content().strip()
                if subcategory_text:
                    subcategories_data.append({
                        'brand': category_item['brand'],
                        'year': category_item['year'],
                        'model': category_item['model'],
                        'submodel': category_item['submodel'],
                        'category': category_item['category'],
                        'subcategory': subcategory_text,
                        'subcategory_div': subcategory_div
                    })
        except Exception as e:
            logger.warning(f"Error collecting subcategories: {e}")
    
    logger.info(f'Found {len(subcategories_data)} subcategories, clicking all...')
    
    click_count = 0
    for subcategory_item in subcategories_data:
        try:
            subcategory_icon = subcategory_item['subcategory_div'].locator('td.niconspace a').first
            click_with_js(page, subcategory_icon)
            click_count += 1
            if click_count % 50 == 0:
                logger.info(f'Clicked {click_count}/{len(subcategories_data)} subcategories')
        except Exception as e:
            logger.warning(f"Failed to click subcategory: {e}")
    
    return subcategories_data


def extract_all_parts(page, context, subcategories_data):
    """Extract all parts from all subcategories"""
    parts_final_list = []
    
    for idx, subcategory_item in enumerate(subcategories_data):
        if idx % 10 == 0:
            logger.info(f'Processing subcategory {idx+1}/{len(subcategories_data)}')
        
        try:
            subcategory_div = subcategory_item['subcategory_div']
            
            # Try to find parts container
            parts_group_div = subcategory_div.locator(
                '> div.nchildren > div.listings-container > form > div.listing-container-border > div > table'
            ).first
            
            part_divs = parts_group_div.locator('> tbody.listing-inner').all()
            logger.info(f"Found {len(part_divs)} parts in {subcategory_item['subcategory']}")
            
            for part_div in part_divs:
                part_dict = extract_part_data(part_div, subcategory_item, context, page)
                if part_dict:
                    parts_final_list.append(part_dict)
                    
        except Exception as e:
            logger.warning(f"Error extracting parts from subcategory: {e}")
    
    return parts_final_list


def extract_part_data(part_div, subcategory_item, context, page):
    """Extract all data for a single part"""
    try:
        part_label = part_div.locator('span.listing-final-manufacturer').first
        part_text = part_label.text_content().strip()
        
        if not part_text:
            return None
        
        part_div_id = part_div.get_attribute('id')
        
        part_number = part_div.locator('span.listing-final-partnumber').first.text_content().strip()
        manufacturer = part_div.locator('span.listing-final-manufacturer').first.text_content().strip()
        
        images_link = None
        if part_div.locator('img.listing-inline-image').count() > 0:
            images_link = part_div.locator('img.listing-inline-image').first.get_attribute('src')
        
        name = None
        if part_div.locator('span.span-link-underline-remover').count() > 0:
            name = part_div.locator('span.span-link-underline-remover').first.text_content().strip()
        
        base_price = None
        stock_status = True
        if part_div.locator('span.listing-total').count() > 0:
            text = part_div.locator('span.listing-total').first.text_content().strip()
            matches = re.findall(r'\d+\.?\d*', text)
            base_price = matches[0] if matches else text
            if base_price == 'Out of Stock':
                stock_status = False
        
        currency = None
        if part_div.locator('span.listing-total').count() > 0:
            currency = part_div.locator('span.listing-total').first.text_content().strip().split(r'+d')[0]
        
        pack_size = None
        if part_div.locator('span.pack_size_box').count() > 0:
            pack_size = part_div.locator('span.pack_size_box').first.text_content().strip()
        
        # Extract description and attributes
        attributes = None
        description = None
        if part_div.locator('a.ra-btn-moreinfo').count() > 0:
            try:
                info_btn = part_div.locator('a.ra-btn-moreinfo').first
                with context.expect_page() as new_page_info:
                    info_btn.click()
                new_page = new_page_info.value
                new_page.wait_for_load_state(state='domcontentloaded')
                new_page_html_content = new_page.content()
                new_page.close()
                attributes, description = extract_description_and_attributes(new_page_html_content)
            except Exception as e:
                logger.warning(f'Error extracting details: {e}')
        
        return {
            'part_number': part_number,
            'manufacturer': manufacturer,
            'category': subcategory_item['category'],
            'subcategory': subcategory_item['subcategory'],
            'images_link': images_link,
            'attributes': attributes,
            'car_manufacturer': subcategory_item['brand'],
            'car_year': subcategory_item['year'],
            'car_model': subcategory_item['model'],
            'car_submodel': subcategory_item['submodel'],
            'name': name,
            'description': description,
            'base_price': base_price,
            'currency': currency,
            'available_quantity': 'tobescraped' if stock_status else None,
            'stock_status': stock_status,
            'supplier_sku': 'to be determined later with the client',
            'pack_size': pack_size
        }
    except Exception as e:
        logger.error(f"Error extracting part data: {e}")
        return None


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
    
    description = None
    if description_div:
        description_text = description_div.find(text=True, recursive=False)
        description = description_text.strip() if description_text else None
    
    attributes = None
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
                attributes[attr_name] = attr_value
    
    return attributes, description


if __name__ == "__main__":
    click_elements_by_car_brand()