from __future__ import annotations

import dlt

from tadawul.scraper.company import CompanyScraper
from tadawul.utils.discovered_company_symbols import (
    MAIN_MARKET_SYMBOLS,
    NOMU_SYMBOLS,
)


@dlt.resource(
    name="raw_company",
    write_disposition="merge",
    primary_key=["symbol", "language"],
)
def company_resource(
    symbol: str,
    language: str,
    scraper: CompanyScraper,
):
    result = scraper.scrape(symbol)

    result["symbol"] = symbol

    yield result


def main():
    pipeline = dlt.pipeline(
        pipeline_name="tadawul_company",
        destination="postgres",
        dataset_name="raw_tadawul",
    )

    # companies = MAIN_MARKET_SYMBOLS
    companies = NOMU_SYMBOLS

    for language in ["en", "ar"]:
        with CompanyScraper(
            headless=True,
            language=language,
        ) as scraper:

            for symbol in companies:
                print(
                    f"Scraping {symbol} - {language}"
                )

                load_info = pipeline.run(
                    company_resource(
                        symbol,
                        language,
                        scraper,
                    )
                )

                print(load_info)


if __name__ == "__main__":
    main()