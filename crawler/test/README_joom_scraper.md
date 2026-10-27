# Joom Category Scraper

Standalone Python script to scrape product information from Joom category pages using the **Scrapling** library.

## Installation

```bash
pip install -r requirements_joom.txt
playwright install chromium
```

## Usage

```python
import asyncio
from joom_category_scraper import scrape_joom_category

async def main():
    category_url = "https://www.joom.com/en/category/mens-fashion/c.1597236266669222893-190-2-2-2152716438"
    products = await scrape_joom_category(category_url, max_products=20)
    
    for product in products:
        print(f"{product['product_name']} - {product['price']} {product['currency']}")

asyncio.run(main())
```

Or run directly:

```bash
python joom_category_scraper.py
```

## Features

- Uses **Scrapling** with StealthyFetcher for anti-detection
- Fallback to regular Fetcher if StealthyFetcher fails
- Handles Cloudflare challenges automatically
- Extracts product name, price, currency, description, image URL, and product URL
- Configurable maximum products to scrape
- Async/await for efficient concurrent scraping

## Output Format

Each product is returned as a dictionary:

```python
{
    "product_name": "Men's Fashion T-Shirt",
    "product_description": "Comfortable cotton blend...",
    "product_url": "https://www.joom.com/en/product/...",
    "price": 12.99,
    "currency": "USD",
    "main_image_url": "https://img.joomcdn.net/..."
}
```

## Requirements

- Python 3.10+
- Scrapling with fetchers extra: `pip install "scrapling[fetchers]"`
- Playwright Chromium: `playwright install chromium`

## Notes

- The scraper uses CSS selectors that match Joom's current page structure
- Selectors may need updates if Joom changes their HTML structure
- Respects rate limits and includes polite delays
- For production use, consider adding proxy rotation and more sophisticated anti-detection measures