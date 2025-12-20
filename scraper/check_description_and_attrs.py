from playwright.sync_api import sync_playwright
from main import logger
from bs4 import BeautifulSoup
import time
import csv
import sys
import threading

def check_description(part_url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(part_url)
            time.sleep(5)  # wait for the page to load completely
            description_element = page.query_selector('div#tab-description')
            description_text = description_element.inner_text()
            logger.info(f'Description text: {description_text}')
            return description_text
        except Exception as e:
            logger.error(f'Error while checking description: {e}')
            return None
        finally:
            context.close()
            browser.close()


def test_check_description_and_attributes():

    start_time = time.perf_counter()

    part_url = 'https://www.rockauto.com/en/moreinfo.php?pk=15097217&cc=951060&pt=8900&jsn=14500'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(part_url)
        time.sleep(5)

        html_content = page.content()

        soup = BeautifulSoup(html_content, 'html.parser')
        description_div = soup.find('section', {'aria-label': lambda x: x and x.startswith('More Information for')})

        if description_div:
            description_text = description_div.find(text=True, recursive=False)
            description_text = description_text.strip() if description_text else 'No description text found'
            logger.info(f'Description text from BeautifulSoup: {description_text}')
        else:
            logger.error('Description div not found using BeautifulSoup')

        attributes_div = soup.find('section', {'aria-label': lambda x: x and 'Specifications' in x})
        if attributes_div:
            attr_table = attributes_div.select_one('table > tbody')
            attr_rows = attr_table.find_all('tr') if attr_table else []
            for row in attr_rows:
                cols = row.find_all('td')
                if len(cols) == 2:
                    attr_name = cols[0].get_text(strip=True)
                    attr_value = cols[1].get_text(strip=True)
                    logger.info(f'Attribute: {attr_name} => Value: {attr_value}')

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    logger.info(f'Test completed in {elapsed_time:.2f} seconds')



def check_description_and_attributes_through_requests(url):   #  main function for now
    import requests
    import sys
    import json

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logger.error(f'Failed to fetch the page, status code: {response.status_code}')
        return
    html_content = response.content

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
        attr_table = attributes_div.select_one('table')
        logger.info(f'Attributes table HTML: {attr_table}')
        attr_rows = attr_table.find_all('tr') if attr_table else []
        logger.info(f'Found {len(attr_rows)} attribute rows')
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


def do_dirty(urls):
    error_urls = []
    for i, url in enumerate(urls):
        print(f'{i}: {url}', file=sys.stderr)
        try:
            check_description_and_attributes_through_requests(url)
        except Exception as e:
            error_urls.append({ 'url': url, 'error': e})
    print(f'Urls: {len(urls)}')
    print(f'Errors: {len(error_urls)}\n=================')
    for error_url in error_urls:
        print(f"{error_url['url']}: {error_url['error']}")

def read_urls(start, count):
    urls = []
    with open('rockauto_parts.csv', 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < start:
                continue
            if i >= count + start:
                break
            urls.append(row['info_link'])
    return urls

if __name__ == '__main__':
    thread_count = 1
    chunk_size = 300

    urls = []
    for i in range(thread_count):
        urls.append(read_urls(i * chunk_size, chunk_size))

    threads = [threading.Thread(target=do_dirty, args=(urls[i],)) for i in range(thread_count)]

    start = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    end = time.time()
    print(f'Thread count: {thread_count}\nChunk_size: {chunk_size}\nTime: {end - start}s')