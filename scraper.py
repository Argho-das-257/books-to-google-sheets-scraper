import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# Google Sheet connection
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("BookScraper").sheet1
except Exception as e:
    print(f"Error connecting to Google Sheets: {e}")
    exit(1)

# Set headers in Google Sheet
try:
    sheet.update(range_name="A1:C1", values=[["Book Name", "Price", "Link"]])
except Exception as e:
    print(f"Error setting headers in Google Sheet: {e}")
    exit(1)

# Website base URL and headers
base_url = "https://books.toscrape.com/catalogue/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

def scrape_page(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        books = soup.find_all("article", class_="product_pod")
        book_data = []
        for book in books:
            name = book.find("h3").find("a")["title"].strip()
            price = book.find("p", class_="price_color").text.strip()
            relative_link = book.find("h3").find("a")["href"]
            link = base_url + relative_link.lstrip("./")  # Handle relative links correctly
            book_data.append([name, price, link])
        return book_data
    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return []
    except AttributeError as e:
        print(f"Error parsing HTML on {url}: {e}")
        return []

all_books = []
page = 1
while True:
    url = f"{base_url}page-{page}.html"  # Correct pagination URL
    print(f"Scraping page {page}...")
    books = scrape_page(url)
    if not books:
        break
    all_books.extend(books)
    page += 1
    time.sleep(1)  # Respectful delay to avoid overloading the server

# Write data to Google Sheet
if all_books:
    try:
        sheet.append_rows(all_books, value_input_option="RAW")
        print(f"Successfully wrote {len(all_books)} books to Google Sheet.")
    except Exception as e:
        print(f"Error writing to Google Sheet: {e}")
else:
    print("No books were scraped.")