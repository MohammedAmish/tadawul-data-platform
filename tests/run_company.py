from tadawul.discovery.ticker_loader import TickerLoader
from tadawul.ingestion.company_scraper import CompanyScraper


loader = TickerLoader(
    "data/tickerData.json"
)

company = loader.get_company("2222")

print("Company:")
print(company)

scraper = CompanyScraper(
    headless=False
)

scraper.scrape(company)