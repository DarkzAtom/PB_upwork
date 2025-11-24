import requests
from bs4 import BeautifulSoup

def scrape_years_insides(brand, year):
    url = f"https://www.rockauto.com/en/catalog/{brand},{year}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        with open('scraped_years_insides.html', 'w', encoding='utf-8') as file:
            file.write(soup.prettify())
        print("Year inside content saved to 'scraped_years_insides.html'")
        return soup
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

if __name__ == "__main__":
    brand = "apollo"
    year = "1965"
    soup = scrape_years_insides(brand, year)
    if soup:
        print(soup.prettify())
    else:
        print("Failed to retrieve the year inside content.")