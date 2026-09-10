import json

from tadawul.discovery.ticker_loader import TickerLoader
from tadawul.scraper.company import CompanyScraper


def main():
    symbol = "9634"

    loader = TickerLoader(
        "data/tickerData.json"
    )

    company = loader.get_by_symbol(symbol)

    if company is None:
        raise ValueError(
            f"Company with symbol {symbol} was not found."
        )

    scraper = CompanyScraper(
        headless=True
    )

    result = scraper.scrape(company)

    company_name = result["company_name"]

    output_path = f"data/{company_name}_{symbol}.json"

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Company: {company_name}")
    print(f"Symbol: {symbol}")
    print(f"Result saved to: {output_path}")


if __name__ == "__main__":
    main()