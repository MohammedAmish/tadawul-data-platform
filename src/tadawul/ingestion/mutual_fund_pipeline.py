from __future__ import annotations

import dlt

from tadawul.scraper.mutual_fund import MutualFundScraper


@dlt.resource(
    name="raw_mutual_fund",
    write_disposition="merge",
    primary_key=["symbol", "language"],
)
def mutual_fund_resource(
    language: str,
    scraper: MutualFundScraper,
):
    fund_symbols = [
    "011041",
    "547001",
    "135004",
]

    for symbol in fund_symbols:
        print(
            f"Scraping mutual fund {symbol} - {language}"
        )

        result = scraper.scrape(symbol)

        result["symbol"] = symbol

        yield result


def main():
    pipeline = dlt.pipeline(
        pipeline_name="tadawul_mutual_fund",
        destination="postgres",
        dataset_name="raw_tadawul",
    )

    for language in ["en", "ar"]:
        with MutualFundScraper(
            headless=True,
            language=language,
        ) as scraper:

            load_info = pipeline.run(
                mutual_fund_resource(
                    language,
                    scraper,
                )
            )

            print(load_info)


if __name__ == "__main__":
    main()