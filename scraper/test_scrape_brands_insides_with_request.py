import requests
from bs4 import BeautifulSoup


def scrape_brand_insides(brand):
    base_url = "https://www.rockauto.com/en/catalog/"
    
    try:
        response = requests.get(base_url + brand)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        with open('scraped_brand_insides.html', 'w', encoding='utf-8') as file:
            file.write(soup.prettify()) 
        print("Brand inside content saved to 'scraped_brand_insides.html'")
        return soup
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

if __name__ == "__main__":
    brand = "apollo"  
    soup = scrape_brand_insides(brand)
    if soup:
        print(soup.prettify())  
    else:
        print("Failed to retrieve the brand inside content.")