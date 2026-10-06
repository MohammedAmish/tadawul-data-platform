from __future__ import annotations

import dlt

from tadawul.scraper.reit import ReitScraper


@dlt.resource(
    name="raw_reit",
    write_disposition="merge",
    primary_key=["symbol", "language"],
)
def reit_resource(
    reit: dict,
    language: str,
    scraper: ReitScraper,
):
    result = scraper.scrape(
        reit["url"]
    )

    yield result


def main():
    pipeline = dlt.pipeline(
        pipeline_name="tadawul_reit",
        destination="postgres",
        dataset_name="raw_tadawul",
    )

    for language in ["en", "ar"]:
        with ReitScraper(
            headless=True,
            language=language,
        ) as scraper:

            reits = scraper.get_all_reits()

            for reit in reits:
                print(
                    f"Scraping {reit['reit_name']} - {language}"
                )

                load_info = pipeline.run(
                    reit_resource(
                        reit,
                        language,
                        scraper,
                    )
                )

                print(load_info)


if __name__ == "__main__":
    main()