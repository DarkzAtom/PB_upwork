import requests


cookies = {
    'ab_amx_5': '0',
    'adCode': 'Referer%20www.google.com%20URL%20%2F',
    'mkt_CA': 'true',
    'mkt_MX': 'true',
    'ck': '1',
    'PHPSESSID': 'gpupn2knt8sdcpmvjp8b325so2',
    'mkt_US': 'true',
    'year_2005': 'true',
    'ID': 'f226866af65a6cfad351f85d09403ee1',
    'idlist': 'f226866af65a6cfad351f85d09403ee1',
    'billing': '2927794289',
    'shipping': '2927794289',
    'saved_server': 'eyJuYW1lIjoid3d3NC5yb2NrYXV0by5jb20iLCJkbnMiOiJ3d3c0LnJvY2thdXRvLmNvbSIsInRzIjoiMjAyNS0xMS0yMyAyMzoxMTozMiJ9',
    'lastcathref': 'https%3A%2F%2Fwww.rockauto.com%2Fen%2Fcatalog%2Fstudebaker',
}

headers = {
    'Accept': 'text/plain, */*; q=0.01',
    'Accept-Language': 'ru-RU,ru;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://www.rockauto.com',
    'Referer': 'https://www.rockauto.com/en/catalog/studebaker',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-GPC': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Chromium";v="142", "Brave";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    # 'Cookie': 'ab_amx_5=0; adCode=Referer%20www.google.com%20URL%20%2F; mkt_CA=true; mkt_MX=true; ck=1; PHPSESSID=gpupn2knt8sdcpmvjp8b325so2; mkt_US=true; year_2005=true; ID=f226866af65a6cfad351f85d09403ee1; idlist=f226866af65a6cfad351f85d09403ee1; billing=2927794289; shipping=2927794289; saved_server=eyJuYW1lIjoid3d3NC5yb2NrYXV0by5jb20iLCJkbnMiOiJ3d3c0LnJvY2thdXRvLmNvbSIsInRzIjoiMjAyNS0xMS0yMyAyMzoxMTozMiJ9; lastcathref=https%3A%2F%2Fwww.rockauto.com%2Fen%2Fcatalog%2Fstudebaker',
}

data = {
    'func': 'navnode_fetch',
    'payload': '{"jsn":{"groupindex":"262","tab":"catalog","make":"ROCKNE","nodetype":"make","jsdata":{"markets":[{"c":"US"}],"mktlist":"US","Show":1},"label":"ROCKNE","href":"https://www.rockauto.com/en/catalog/rockne","labelset":true,"ok_to_expand_single_child_node":true,"bring_listings_into_view":true,"loaded":false,"expand_after_load":true,"fetching":true},"max_group_index":2977}',
    'api_json_request': '1',
    'sctchecked': '1',
    'scbeenloaded': 'false',
    'curCartGroupID': '_maincart',
}


def test_curl_bash():
    response = requests.post('https://www.rockauto.com/catalog/catalogapi.php', cookies=cookies, headers=headers, data=data)
    print(response.text)
    with open('test_curl_bash.html', 'w', encoding='utf-8') as file:
        file.write(response.text)
    


if __name__ == "__main__":
    test_curl_bash()