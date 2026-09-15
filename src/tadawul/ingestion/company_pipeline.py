from __future__ import annotations

import dlt

from tadawul.scraper.company import CompanyScraper


MAIN_MARKET_SYMBOLS = [
    "2222",
    "2030",
    "4240",
    "6060",
    "4220",
]

NOMU_SYMBOLS = [
    "9510",
    "9513",
    "9523",
    "9541",
    "9544",
]


@dlt.resource(
    name="raw_company",
    write_disposition="merge",
    primary_key=["symbol", "language"],
)
def company_resource(
    symbol: str,
    language: str,
):
    scraper = CompanyScraper(
        headless=True,
        language=language,
    )

    result = scraper.scrape(symbol)

    result["symbol"] = symbol

    yield result


def main():
    pipeline = dlt.pipeline(
        pipeline_name="tadawul_company",
        destination="postgres",
        dataset_name="raw_tadawul",
    )

    companies = (
        MAIN_MARKET_SYMBOLS
        + NOMU_SYMBOLS
    )

    for symbol in companies:
        for language in ["en", "ar"]:
            print(
                f"\n{'=' * 60}\n"
                f"Loading company {symbol} - "
                f"language: {language}"
                f"\n{'=' * 60}"
            )

            load_info = pipeline.run(
                company_resource(
                    symbol,
                    language,
                )
            )

            print(load_info)


if __name__ == "__main__":
    main()