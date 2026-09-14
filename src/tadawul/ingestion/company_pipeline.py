from __future__ import annotations

import dlt

from tadawul.scraper.company import CompanyScraper


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

    for language in ["en", "ar"]:
        print(
            f"\n{'=' * 60}\n"
            f"Loading company {2222} - language: {language}\n"
            f"{'=' * 60}"
        )

        load_info = pipeline.run(
            company_resource(
                "2222",
                language,
            )
        )

        print(load_info)


if __name__ == "__main__":
    main()