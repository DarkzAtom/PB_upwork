import requests
from bs4 import BeautifulSoup
import sys

cookies = {
    'ID': '0',
    'mkt_US': 'true',
    'mkt_CA': 'true',
    'mkt_MX': 'true',
    'year_2005': 'true',
    'ck': '1',
    'idlist': '0',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Cache-Control': 'max-age=0',
}

params = {
    'mfr': 'valvoline',
    'partnum': '904683',
}

response = requests.get('https://www.rockauto.com/en/partsearch/', params=params, cookies=cookies, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')
nck_input = soup.find('input', {'name': '_nck'})
listing_data_input = soup.find('input', {'name': 'listing_data_essential[3]'})
ssk_input = soup.find('input', {'name': 'ssk[3]'})
        
if nck_input and listing_data_input and ssk_input and nck_input.get('value') and listing_data_input.get('value') and ssk_input.get('value'):
    print('nck: ' + nck_input['value'], file=sys.stderr)
    print('listing_data_essential: ' + listing_data_input['value'], file=sys.stderr)
    print('ssk: ' + ssk_input['value'], file=sys.stderr)
else:
    print("Could not find something", file=sys.stderr)
    exit()


#####################################3

cookies = {
    'ID': '0',
    'mkt_US': 'true',
    'mkt_CA': 'true',
    'mkt_MX': 'true',
    'year_2005': 'true',
    'ck': '1',
    'idlist': '0',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
    'Accept': 'text/plain, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://www.rockauto.com',
    'Sec-GPC': '1',
    'Connection': 'keep-alive',
    'Referer': 'https://www.rockauto.com/en/partsearch/?mfr=' + params['mfr'] + '&partnum=' + params['partnum'],
    # 'Cookie': 'saved_server=eyJuYW1lIjoid3d3NC5yb2NrYXV0by5jb20iLCJkbnMiOiJ3d3c0LnJvY2thdXRvLmNvbSIsInRzIjoiMjAyNS0xMi0xNCAxMTowMTozMSJ9; ID=0; mkt_US=true; mkt_CA=true; mkt_MX=true; year_2005=true; ck=1; lastcathref=https%3A%2F%2Fwww.rockauto.com%2Fen%2Fcatalog%2Faudi%2C2026%2Ca8%2C3.0l%2Bv6%2Bturbocharged%2C3459053%2Ccooling%2Bsystem%2Ccoolant%2B%2F%2Bantifreeze%2C11393; PHPSESSID=ogvitbmitql01ik36428l4fng4; idlist=0',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Priority': 'u=0',
}

NCK=nck_input['value']
FILTER_INPUT=''
OPTION_CHOICE='0-0-0-1'
LISTING_DATA_ESSENTIAL=listing_data_input['value']
SSK=ssk_input['value']
RA_QUANTITY='99999'
HAS_WORKING_JS='1'
ADDPART='1'
FUNC='cart-addpart'
PAYLOAD='%7B%7D'
API_JSON_REQUEST='1'
SCT_CHECKED='1'
SC_BEEN_LOADED='true'
CUR_CART_GROUP_ID='_sidecart'

data = (
'_nck=' + NCK +
'&filterinput=' + FILTER_INPUT +
'&optionchoice%5B3%5D=' + OPTION_CHOICE +
'&listing_data_essential%5B3%5D=' + LISTING_DATA_ESSENTIAL +
'&ssk%5B3%5D=' + SSK +
'&raquantity%5B3%5D=' + RA_QUANTITY +
'&has_working_js=' + HAS_WORKING_JS +
'&addpart[3]=' + ADDPART +
'&func=' + FUNC +
'&payload=' + PAYLOAD +
'&api_json_request=' + API_JSON_REQUEST +
'&sctchecked=' + SCT_CHECKED +
'&scbeenloaded=' + SC_BEEN_LOADED +
'&curCartGroupID=' + CUR_CART_GROUP_ID
)

print(data, file=sys.stderr)

response = requests.post('https://www.rockauto.com/catalog/catalogapi.php', cookies=cookies, headers=headers, data=data)
soup = BeautifulSoup(response.content, 'html.parser')
print(soup.prettify())