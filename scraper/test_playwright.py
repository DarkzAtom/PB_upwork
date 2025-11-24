from playwright.sync_api import sync_playwright
import time 
from bs4 import BeautifulSoup


'''
This will probably be a choice to go. too much pain
in the ass with handling-> parsing every php request from network
'''

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


def click_elements_to_widen_tree():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()

        page = context.new_page()

        page.goto("https://www.rockauto.com/")

        time.sleep(2)

            
        page.locator("[id=\"navicon[9]\"] > a").click()
        page.locator("[id=\"navicon[10]\"] > a").click()
        page.locator("[id=\"navicon[11]\"] > a").click()
        page.locator("[id=\"navicon[12]\"] > a").click()
        
        time.sleep(5)


        page.close()
        context.close()
        browser.close()



if __name__ == "__main__":
    click_elements_to_widen_tree()