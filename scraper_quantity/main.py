import requests
from bs4 import BeautifulSoup
import json
import sys
import csv
from urllib.parse import quote_plus
import time
import threading

def quantity_request(manufacturer: str, part_number: str):
    group_index = "3"

    # ========== FIRST REQUEST ==========
    headers_1 = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=0, i',
    }

    params = {
        'mfr': manufacturer,
        'partnum': part_number,
    }

    # print(f'Manufacturer: {manufacturer}', file=sys.stderr)
    # print(f'Part number: {part_number}\n', file=sys.stderr)

    response_1 = requests.get('https://www.rockauto.com/en/partsearch/', 
                            params=params, 
                            headers=headers_1)

    soup = BeautifulSoup(response_1.content, 'html.parser')

    if soup.find('span', class_='oos-price-text'):
        return None

    nck_input = soup.find('input', {'name': '_nck'})
    listing_data_input = soup.find('input', {'name': f'listing_data_essential[{group_index}]'})
    option_choice = soup.find('input', {'name': f'optionchoice[{group_index}]'})
    ssk_input = soup.find('input', {'name': f'ssk[{group_index}]'})
    jnck_inputs = soup.find_all('input', {'name': '_nck'})
    jnck_input = jnck_inputs[int(group_index)].get('value') if len(jnck_inputs) > int(group_index) else None

    option_choices = []
    container = soup.find('span', id=f'ddrepl[optionchoice[{group_index}]][container]')
    if container:
        option_choices = [option['value'] for option in container.find_all('option') if option.get('value')]
    else:
        if not (option_choice and option_choice.get('value')):
            raise ValueError("No option choice, likely couldn't find the part through part search")
        option_choices.append(option_choice['value'])
    
    # print(option_choices)

    saved_server_cookie = response_1.cookies.get('saved_server', '')

    if not (nck_input and nck_input.get('value')):
        raise ValueError('No nck')

    if not (listing_data_input and listing_data_input.get('value')):
        raise ValueError("No listing_data_essential, likely couldn't find the part through part search")

    if not (ssk_input and ssk_input.get('value')):
        raise ValueError("No ssk, likely couldn't find the part through part search")

    if not jnck_input:
        raise ValueError('No jnck')

    nck_token = nck_input['value']
    listing_data_json = listing_data_input['value']
    ssk_token = ssk_input['value']
    jnck_token = jnck_input

    # print(f'nck: {nck_token[:50]}...', file=sys.stderr)
    # print(f'listing_data: {listing_data_json[:50]}...', file=sys.stderr)
    # print(f'ssk: {ssk_token[:50]}...', file=sys.stderr)
    # print(f'jnck: {jnck_token[:50]}...', file=sys.stderr)
    # print(f'saved_server cookie: {saved_server_cookie[:50]}...', file=sys.stderr)


    # ========== SECOND REQUEST ==========
    quantity = "99999"
    # option_choice_value = "0-0-0-1"

    cookies = {
        'saved_server': saved_server_cookie,
        'ID': '0',
        'idlist': '0',
        'ck': '1',
    }

    headers_2 = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
        'Accept': 'text/plain, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.rockauto.com',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        'Referer': f'https://www.rockauto.com/en/partsearch/?mfr={manufacturer}&partnum={part_number}',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Priority': 'u=0',
    }

    quantities = []
    for option_choice in option_choices:
        data_params = {
            '_nck': nck_token,
            'filterinput': '',
            f'optionchoice[{group_index}]': option_choice,
            f'listing_data_essential[{group_index}]': listing_data_json,
            f'ssk[{group_index}]': ssk_token,
            f'raquantity[{group_index}]': quantity,
            'has_working_js': '1',
            f'addpart[{group_index}]': '1',
            'func': 'cart-addpart',
            'payload': '{}',
            'api_json_request': '1',
            'sctchecked': '1',
            'scbeenloaded': 'true',
            'curCartGroupID': '_sidecart',
            '_jnck': jnck_token,
        }

        response_2 = requests.post('https://www.rockauto.com/catalog/catalogapi.php', 
                                cookies=cookies, 
                                headers=headers_2, 
                                data=data_params)

        # print(response_2.content.decode('utf-8', errors='ignore'))

        # with open(f'scraper_quantity/responses/{output_file_name}_{option_choice}.json', 'w') as f:
        #     json.dump(response_2.json(), f, indent=2)

        main_element = response_2.json()['html_fill_sections']['section-tab-panel-inner-dynamic[cart]']

        quantity_soup = BeautifulSoup(main_element, 'html.parser')
        quantity_element = quantity_soup.find('input', {'aria-label': 'Quantity', 'id': 'raquantity[__GIP__1__]'}).get('value')
        quantities.append(quantity_element)
    
    return quantities

def do_dirty(parts):
    error_parts = []
    for i, part in enumerate(parts):
        print(f'{i}: {part["manufacturer"]} {part["part_number"]}', file=sys.stderr)
        try:
            quantities = quantity_request(quote_plus(part['manufacturer']), part['part_number'])
            # print(quantities)
        except Exception as e:
            # print(f'Some shit happened: {e}', file=sys.stderr)
            error_parts.append({ 'part_number': part['part_number'], 'manufacturer': part['manufacturer'], 'error': e})
    print(f'Parts: {len(parts)}')
    print(f'Errors: {len(error_parts)}\n=================')
    for error_part in error_parts:
        print(f"{error_part['manufacturer']} {error_part['part_number']}: {error_part['error']}")

def read_parts(start, count):
    parts = []
    with open('scraper/rockauto_parts.csv', 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < start:
                continue
            if i >= count + start:
                break
            parts.append({ 'part_number': row['part_number'], 'manufacturer': row['manufacturer'] })
    return parts

if __name__ == '__main__':
    thread_count = 10
    chunk_size = 30

    parts = []
    for i in range(thread_count):
        parts.append(read_parts(i * chunk_size, chunk_size))

    threads = [threading.Thread(target=do_dirty, args=(parts[i],)) for i in range(thread_count)]

    start = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    end = time.time()
    print(f'Thread count: {thread_count}\nChunk_size: {chunk_size}\nTime: {end - start}s')