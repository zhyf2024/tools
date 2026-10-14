from scrapling.fetchers import Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
StealthyFetcher.adaptive = True

page = StealthyFetcher.fetch('https://ingatlan.com/lista/kiado+lakas+ii-ker+xiii-ker', solve_cloudflare=True)
products = page.css('.position-relative', auto_save=True)
print(products)