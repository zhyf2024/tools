"""
Standalone Joom category scraper using Scrapling library.
Scrapes product information from Joom category pages.
"""

import asyncio
import re
from typing import Any

from scrapling.fetchers import Fetcher, StealthyFetcher


JOOM_BASE_URL = "https://www.joom.com"
_BROWSER_FLAGS = ["--no-sandbox", "--disable-dev-shm-usage"]

_CURRENCY_BY_SYMBOL = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "CNY", "₽": "RUB"}


def _first_text(page: Any, selectors: list[str]) -> str | None:
    """Return first non-empty text from prioritized selectors."""
    for selector in selectors:
        nodes = page.css(selector)
        if nodes:
            text = (nodes[0].text or "").strip()
            if text:
                return text
    return None


def _extract_price(page: Any) -> tuple[float, str]:
    """Extract price and currency from page."""
    for selector in ["span[data-qa='product-price']", "[data-qa*='price']", "[class*='price']"]:
        nodes = page.css(selector)
        if not nodes:
            continue
        text = (nodes[0].text or "").strip()
        match = re.search(r"\d+(?:[.,]\d+)?", text.replace(",", ""))
        if not match:
            continue
        currency = next((code for symbol, code in _CURRENCY_BY_SYMBOL.items() if symbol in text), "USD")
        try:
            return float(match.group()), currency
        except ValueError:
            continue
    return 0.0, "USD"


def _extract_image(page: Any) -> str | None:
    """Extract main product image URL."""
    for selector in ["img[data-qa='product-image']", "img[data-qa*='image']", "[class*='gallery'] img", "img[src*='joom']"]:
        for node in page.css(selector):
            src = (node.attrib.get("src") or "").strip()
            if src.startswith("http"):
                return src
    return None


def _fetch_page_sync(url: str) -> Any:
    """Fetch page using Scrapling with fallback strategies."""
    errors: list[str] = []
    fetchers = (
        ("StealthyFetcher", lambda: StealthyFetcher.fetch(url, headless=True, extra_flags=_BROWSER_FLAGS)),
        ("Fetcher", lambda: Fetcher.get(url)),
    )
    for name, fetch in fetchers:
        try:
            return fetch()
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            print(f"Warning: Scrapling {name} fetch failed: {url}, error: {exc}")
    raise RuntimeError(f"Failed to fetch page: {url}; " + "; ".join(errors))


async def fetch_page(url: str) -> Any:
    """Async wrapper for page fetching."""
    return await asyncio.to_thread(_fetch_page_sync, url)


def extract_product_links(page: Any) -> list[str]:
    """Extract product detail links from category page."""
    anchors = page.css("a.J-spProductCardProductCardProductCardLink")
    if not anchors:
        anchors = page.css('a[href*="/product"]')

    links: list[str] = []
    seen: set[str] = set()
    for anchor in anchors:
        href = (anchor.attrib.get("href") or "").strip()
        if not href:
            continue
        if href.startswith("/"):
            href = f"{JOOM_BASE_URL}{href}"
        if "joom.com" not in href or "/product" not in href:
            continue
        if href in seen:
            continue
        seen.add(href)
        links.append(href)
    return links


async def scrape_single_product(product_url: str) -> dict[str, Any] | None:
    """Scrape detailed information for a single product."""
    try:
        page = await fetch_page(product_url)
        if getattr(page, "status", None) != 200:
            print(f"Warning: Failed to fetch product: {product_url}, status: {getattr(page, 'status', None)}")
            return None

        price, currency = _extract_price(page)
        return {
            "product_name": _first_text(page, ["h1[data-qa='product-title']", "h1"]) or "Unknown Product",
            "product_description": _first_text(page, ["div[data-qa='product-description']", "[class*='description']"]),
            "product_url": product_url,
            "price": price,
            "currency": currency,
            "main_image_url": _extract_image(page),
        }
    except Exception as exc:
        print(f"Error scraping product {product_url}: {exc}")
        return None


async def scrape_joom_category(category_url: str, max_products: int = 20) -> list[dict[str, Any]]:
    """
    Scrape products from a Joom category page.

    Args:
        category_url: Joom category URL (e.g., "https://www.joom.com/en/category/mens-fashion/c.1597236266669222893-190-2-2-2152716438")
        max_products: Maximum number of products to scrape

    Returns:
        List of product dictionaries with name, description, url, price, currency, and image_url
    """
    print(f"Starting scrape of Joom category: {category_url}, max products: {max_products}")

    page = await fetch_page(category_url)
    product_links = extract_product_links(page)

    if not product_links:
        print(f"Warning: No product links found on category page: {category_url}")
        return []

    print(f"Found {len(product_links)} product links")

    products: list[dict[str, Any]] = []
    for product_url in product_links:
        if len(products) >= max_products:
            break

        product_data = await scrape_single_product(product_url)
        if product_data:
            products.append(product_data)
            print(f"Scraped: {product_data['product_name']} - {product_data['price']} {product_data['currency']}")

    print(f"Scraping complete. Total products scraped: {len(products)}")
    return products


async def main():
    """Main function to demonstrate usage."""
    category_url = "https://www.joom.com/en/category/mens-fashion/c.1597236266669222893-190-2-2-2152716438"
    products = await scrape_joom_category(category_url, max_products=10)

    print("\n=== Scraped Products ===")
    for i, product in enumerate(products, 1):
        print(f"{i}. {product['product_name']}")
        print(f"   Price: {product['price']} {product['currency']}")
        print(f"   URL: {product['product_url']}")
        print(f"   Image: {product['main_image_url']}")
        print(f"   Description: {product['product_description'][:100] if product['product_description'] else 'N/A'}...")
        print()


if __name__ == "__main__":
    asyncio.run(main())