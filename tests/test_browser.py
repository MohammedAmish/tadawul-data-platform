import json

from tadawul.discovery.ticker_loader import TickerLoader
from tadawul.scraper.company import CompanyScraper


def main():
    loader = TickerLoader(
        "data/tickerData.json"
    )

    company = loader.get_by_symbol("2222")

    if company is None:
        raise ValueError(
            "Company 2222 was not found."
        )

    scraper = CompanyScraper(
        headless=False
    )

    result = scraper.scrape(company)

    output_path = "data/aramco_2222.json"

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

    print(
        f"Result saved to: {output_path}"
    )


if __name__ == "__main__":
    main()