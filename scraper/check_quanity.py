import requests 
from bs4 import BeautifulSoup

def test_curl_bash():

    cookies = {
        'adCode': 'Referer%20search.brave.com%20URL%20%2F',
        'mkt_CA': 'true',
        'mkt_MX': 'true',
        'ck': '1',
        'PHPSESSID': 'cp7qanvkq545ijp358mushhts7',
        'year_2005': 'true',
        'mkt_US': 'true',
        'lastcathref': 'https%3A%2F%2Fwww.rockauto.com%2Fen%2Fcatalog%2Fbmw%2C2009%2C135i%2C3.0l%2Bl6%2Bturbocharged%2C1443134%2Ccooling%2Bsystem%2Cradiator%2C2172',
        'saved_server': 'eyJuYW1lIjoid3d3NC5yb2NrYXV0by5jb20iLCJkbnMiOiJ3d3c0LnJvY2thdXRvLmNvbSIsInRzIjoiMjAyNS0xMi0wOSAxNTo0NTowNiJ9',
        'ID': '0',
        'idlist': '0',
    }

    headers = {
        'Accept': 'text/plain, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.6',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.rockauto.com',
        'Referer': 'https://www.rockauto.com/en/catalog/bmw,2009,135i,3.0l+l6+turbocharged,1443134,cooling+system,radiator,2172',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Brave";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        # 'Cookie': 'adCode=Referer%20search.brave.com%20URL%20%2F; mkt_CA=true; mkt_MX=true; ck=1; PHPSESSID=cp7qanvkq545ijp358mushhts7; year_2005=true; mkt_US=true; lastcathref=https%3A%2F%2Fwww.rockauto.com%2Fen%2Fcatalog%2Fbmw%2C2009%2C135i%2C3.0l%2Bl6%2Bturbocharged%2C1443134%2Ccooling%2Bsystem%2Cradiator%2C2172; saved_server=eyJuYW1lIjoid3d3NC5yb2NrYXV0by5jb20iLCJkbnMiOiJ3d3c0LnJvY2thdXRvLmNvbSIsInRzIjoiMjAyNS0xMi0wOSAxNTo0NTowNiJ9; ID=0; idlist=0',
    }

    data = '_nck=Ekt6BqBF1pwlXdx0gYlm1XyS%2BrEifIwvxWIl7Mt9zft%2BWrd9NkObIGqu3S%2B6bg%2F7X6a3bS27cXOPEJnu%2BQ0XlI4D6Cb%2F3TwsfyqSNZhInvy0ylPDRFA4ECbo6dr%2F2P%2FN40ifmJPncLTKaE26SYg9HFIK6oJy%2FF4kQ9c3c9N7ZODbw4dX%2BqBuDckfw%2BNkwrNrIx52EAnq4%2FAn5UxDLsv8OoxOt1ZnLbJBkl774o4A9Z6pNBtdLj%2Bo6uRsUhhpZqJgxYQ3Gwh4HR1s%2FhbWABHfil0mdXS%2FV9jwy9fIM0EYHFe0OdxfeEextOh7xNkbEvLZykRchf02%2Bx7S7yOLDY0xWoC6x29zci5w3gF%2Fe%2BY8JTdIuUDNkzb4hhQIBDT7S1qptK4R2mJWlRVpFpS4fpOVDheGuhECFd0aQxwIkxrPkh5aUMJbZvm0eGcrmqC4ZNxH9humk2bcSde7mz1fj1GAF6DMpxFaIWZmSKxLbfaCEA1ipncEcY8XONCaGlX8CjSajZ8cai69Bm3jak6vPuCul%2BeXsfqof%2FeT5A4eGkKXIeonGT%2FCOYkGtpiH1lYZlfSSD4NvZHvI5Eh3glmp9c%2FUmrRwBLGvyScr&filterinput=&filtercodekey%5B12373%5D=US&filtercodekey%5B12373%5D=CA&filtercodekey%5B12373%5D=MX&optionchoice%5B12374%5D=0-0-0-1&listing_data_essential%5B12374%5D=%7B%22groupindex%22%3A%2212374%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%228612620%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%227031%22%2C%22whpartnum%22%3A%22C3+3717%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12374%5D=122540%2CUS%2CCA%2CMX&ssk%5B12374%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12374%5D=99999&optionchoice%5B12375%5D=0-0-0-1&listing_data_essential%5B12375%5D=%7B%22groupindex%22%3A%2212375%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%2210117608%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2277478%22%2C%22whpartnum%22%3A%22USC+2941%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12375%5D=122540%2CUS%2CCA&ssk%5B12375%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12375%5D=1&optionchoice%5B12376%5D=0-0-0-1&listing_data_essential%5B12376%5D=%7B%22groupindex%22%3A%2212376%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%228612616%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2210462%22%2C%22whpartnum%22%3A%22C3+3716%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12376%5D=122544%2CUS%2CMX&ssk%5B12376%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12376%5D=1&optionchoice%5B12377%5D=0-0-0-1&listing_data_essential%5B12377%5D=%7B%22groupindex%22%3A%2212377%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%221373430%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2230073%22%2C%22whpartnum%22%3A%22TY+2941%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12377%5D=US%2CCA&ssk%5B12377%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12377%5D=1&optionchoice%5B12378%5D=0-0-0-1&listing_data_essential%5B12378%5D=%7B%22groupindex%22%3A%2212378%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%2211709729%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2228027%22%2C%22whpartnum%22%3A%22UAC+RA-2973C%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12378%5D=US%2CCA%2CMX&ssk%5B12378%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12378%5D=1&optionchoice%5B12379%5D=0-0-0-1&listing_data_essential%5B12379%5D=%7B%22groupindex%22%3A%2212379%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%223759900%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2233013%22%2C%22whpartnum%22%3A%22OSC+2973%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12379%5D=122544%2CUS%2CMX&ssk%5B12379%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12379%5D=1&optionchoice%5B12380%5D=0-0-0-1&listing_data_essential%5B12380%5D=%7B%22groupindex%22%3A%2212380%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%221251238%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2290660%22%2C%22whpartnum%22%3A%22SQ+CU2941%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12380%5D=122540%2CUS%2CCA%2CMX&ssk%5B12380%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12380%5D=1&optionchoice%5B12381%5D=0-0-0-1&listing_data_essential%5B12381%5D=%7B%22groupindex%22%3A%2212381%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%2211524417%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2211051%22%2C%22whpartnum%22%3A%22GPD+2882C%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12381%5D=122540%2CUS%2CCA%2CMX&ssk%5B12381%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12381%5D=1&optionchoice%5B12382%5D=0-0-0-1&listing_data_essential%5B12382%5D=%7B%22groupindex%22%3A%2212382%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%2211982893%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2292521%22%2C%22whpartnum%22%3A%22KO+A2882%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12382%5D=US%2CCA%2CMX&ssk%5B12382%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12382%5D=1&optionchoice%5B12383%5D=0-0-0-1&listing_data_essential%5B12383%5D=%7B%22groupindex%22%3A%2212383%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%224932522%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2276010%22%2C%22whpartnum%22%3A%22AY+8012973%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12383%5D=122544%2CUS%2CMX&ssk%5B12383%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12383%5D=1&optionchoice%5B12384%5D=0-0-0-1&listing_data_essential%5B12384%5D=%7B%22groupindex%22%3A%2212384%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%225614416%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2276010%22%2C%22whpartnum%22%3A%22AY+8012941%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12384%5D=122540%2CUS%2CCA%2CMX&ssk%5B12384%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12384%5D=1&optionchoice%5B12385%5D=0-0-0-1&listing_data_essential%5B12385%5D=%7B%22groupindex%22%3A%2212385%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%225551161%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%227031%22%2C%22whpartnum%22%3A%22N1+60832%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12385%5D=US%2CCA%2CMX&ssk%5B12385%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12385%5D=1&optionchoice%5B12386%5D=0-0-0-1&listing_data_essential%5B12386%5D=%7B%22groupindex%22%3A%2212386%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%224013247%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%227031%22%2C%22whpartnum%22%3A%22N1+60785A%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12386%5D=US%2CCA%2CMX&ssk%5B12386%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12386%5D=1&optionchoice%5B12387%5D=0-0-0-1&listing_data_essential%5B12387%5D=%7B%22groupindex%22%3A%2212387%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%224819140%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%227031%22%2C%22whpartnum%22%3A%22M1+CR1085000P%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12387%5D=122544%2CUS%2CMX&ssk%5B12387%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12387%5D=1&optionchoice%5B12388%5D=0-0-0-1&listing_data_essential%5B12388%5D=%7B%22groupindex%22%3A%2212388%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%226080178%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2210462%22%2C%22whpartnum%22%3A%22M1+CR1923000P%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12388%5D=US%2CCA%2CMX&ssk%5B12388%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12388%5D=1&optionchoice%5B12389%5D=0-0-0-1&listing_data_essential%5B12389%5D=%7B%22groupindex%22%3A%2212389%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%2215878917%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2221076%22%2C%22whpartnum%22%3A%22VM+V20-60-0006%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12389%5D=122544%2CUS%2CMX&ssk%5B12389%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12389%5D=1&optionchoice%5B12390%5D=0-0-0-1&listing_data_essential%5B12390%5D=%7B%22groupindex%22%3A%2212390%22%2C%22carcode%22%3A%221443134%22%2C%22parttype%22%3A%222172%22%2C%22partkey%22%3A%2215754061%22%2C%22opts%22%3A%7B%220-0-0-1%22%3A%7B%22warehouse%22%3A%2231217%22%2C%22whpartnum%22%3A%22GP+2973C%22%2C%22optionlist%22%3A%220%22%2C%22paramcode%22%3A%220%22%2C%22notekey%22%3A%220%22%2C%22multiple%22%3A%221%22%7D%7D%7D&listing-codekey%5B12390%5D=122544%2CUS%2CMX&ssk%5B12390%5D=HPc6NY4sqMvPDBCrBav8qRqZExH26Yzk7Rdj4r%2BD7c%2F7j04gADemJ9uqF%2FQO2ggf1QBdc2%2F5xzk%3D&raquantity%5B12390%5D=1&has_working_js=1&has_working_js=1&has_working_js=1&addpart[12374]=1&func=cart-addpart&payload=%7B%7D&api_json_request=1&sctchecked=1&scbeenloaded=true&curCartGroupID=_sidecart'

    response = requests.post('https://www.rockauto.com/catalog/catalogapi.php', cookies=cookies, headers=headers, data=data)


    import json


    with open('scraper/response.json', 'w') as f:
        json.dump(response.json(), f, indent=4)

    with open('scraper/response.json', 'r') as f:
        resp_json = json.load(f)

    main_element = resp_json['html_fill_sections']['section-tab-panel-inner-dynamic[cart]']

    quantity_soup = BeautifulSoup(main_element, 'html.parser')
    quantity_element = quantity_soup.find('input', {'aria-label': 'Quantity', 'id': 'raquantity[__GIP__1__]'}).get('value')

    last_value = '711'


    print(main_element)
    print(quantity_element)

    


if __name__ == '__main__':
    test_curl_bash()

