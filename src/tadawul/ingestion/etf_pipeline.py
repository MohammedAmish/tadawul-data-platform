from __future__ import annotations

import dlt

from tadawul.scraper.etf import EtfScraper


@dlt.resource(
    name="raw_etf",
    write_disposition="merge",
    primary_key=["symbol", "language"],
)
def etf_resource(
    language: str,
    scraper: EtfScraper,
):
    etfs = scraper.get_all_etfs()

    for etf in etfs:
        print(
            f"Scraping ETF {etf['name']} - {language}"
        )

        result = scraper.scrape(
            etf["url"]
        )

        yield result


def main():
    pipeline = dlt.pipeline(
        pipeline_name="tadawul_etf",
        destination="postgres",
        dataset_name="raw_tadawul",
    )

    for language in ["en", "ar"]:
        with EtfScraper(
            headless=True,
            language=language,
        ) as scraper:

            load_info = pipeline.run(
                etf_resource(
                    language,
                    scraper,
                )
            )

            print(load_info)


if __name__ == "__main__":
    main()