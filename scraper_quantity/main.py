import requests
from bs4 import BeautifulSoup
import json
import sys

# THESE TWO LINES ARE CONFIGURATION
manufacturer = "CARLSON"
part_number = "H835"

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

print(f'Manufacturer: {manufacturer}', file=sys.stderr)
print(f'Part number: {part_number}\n', file=sys.stderr)

response_1 = requests.get('https://www.rockauto.com/en/partsearch/', 
                          params=params, 
                          headers=headers_1)

soup = BeautifulSoup(response_1.content, 'html.parser')

nck_input = soup.find('input', {'name': '_nck'})
listing_data_input = soup.find('input', {'name': f'listing_data_essential[{group_index}]'})
ssk_input = soup.find('input', {'name': f'ssk[{group_index}]'})
jnck_inputs = soup.find_all('input', {'name': '_nck'})
jnck_input = jnck_inputs[int(group_index)].get('value') if len(jnck_inputs) > int(group_index) else None

saved_server_cookie = response_1.cookies.get('saved_server', '')

if not (nck_input and nck_input.get('value')):
    print('ERROR: Could not find nck', file=sys.stderr)
    sys.exit(1)

if not (listing_data_input and listing_data_input.get('value')):
    print('ERROR: Could not find listing_data_essential', file=sys.stderr)
    sys.exit(1)

if not (ssk_input and ssk_input.get('value')):
    print('ERROR: Could not find ssk', file=sys.stderr)
    sys.exit(1)

if not jnck_input:
    print('ERROR: Could not find jnck', file=sys.stderr)
    sys.exit(1)

nck_token = nck_input['value']
listing_data_json = listing_data_input['value']
ssk_token = ssk_input['value']
jnck_token = jnck_input

print(f'nck: {nck_token[:50]}...', file=sys.stderr)
print(f'listing_data: {listing_data_json[:50]}...', file=sys.stderr)
print(f'ssk: {ssk_token[:50]}...', file=sys.stderr)
print(f'jnck: {jnck_token[:50]}...', file=sys.stderr)
print(f'saved_server cookie: {saved_server_cookie[:50]}...', file=sys.stderr)


# ========== SECOND REQUEST ==========
quantity = "99999"
option_choice_value = "0-0-0-1"

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

data_params = {
    '_nck': nck_token,
    'filterinput': '',
    f'optionchoice[{group_index}]': option_choice_value,
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

print(response_2.content.decode('utf-8', errors='ignore'))

with open('scraper_quantity/response.json', 'w') as f:
    json.dump(response_2.json(), f, indent=2)