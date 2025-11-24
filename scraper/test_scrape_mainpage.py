import requests
from bs4 import BeautifulSoup


def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  
        soup = BeautifulSoup(response.text, 'html.parser')
        with open('scraped_content.html', 'w', encoding='utf-8') as file:
            file.write(soup.prettify()) 
        print("Website content saved to 'scraped_content.html'")
        return soup
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

if __name__ == "__main__":
    url = "https://www.rockauto.com/"
    soup = scrape_website(url)
    if soup:
        print(soup.prettify())  
    else:
        print("Failed to retrieve the website content.")