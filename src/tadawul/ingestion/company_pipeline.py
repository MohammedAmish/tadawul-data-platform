from __future__ import annotations

import dlt

from tadawul.discovery.ticker_loader import TickerLoader
from tadawul.scraper.company import CompanyScraper


@dlt.resource(
    name="raw_company",
    write_disposition="merge",
    primary_key="symbol",
)
def company_resource(symbol: str):
    loader = TickerLoader("data/tickerData.json")

    company = loader.get_by_symbol(symbol)

    if company is None:
        raise ValueError(
            f"Company {symbol} was not found in tickerData.json."
        )

    scraper = CompanyScraper(
        headless=True
    )

    result = scraper.scrape(company)

    result["symbol"] = symbol

    yield result


def main():
    pipeline = dlt.pipeline(
        pipeline_name="tadawul_company",
        destination="postgres",
        dataset_name="raw_tadawul",
    )

    load_info = pipeline.run(
        company_resource("2222")
    )

    print(load_info)


if __name__ == "__main__":
    main()