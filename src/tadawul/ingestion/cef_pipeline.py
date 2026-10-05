from __future__ import annotations

import dlt

from tadawul.scraper.cef import CefScraper


@dlt.resource(
    name="raw_cef",
    write_disposition="merge",
    primary_key=["symbol", "language"],
)
def cef_resource(
    cef: dict,
    language: str,
    scraper: CefScraper,
):
    result = scraper.scrape(
        cef["url"]
    )

    yield result


def main():
    pipeline = dlt.pipeline(
        pipeline_name="tadawul_cef",
        destination="postgres",
        dataset_name="raw_tadawul",
    )

    for language in ["en", "ar"]:
        with CefScraper(
            headless=True,
            language=language,
        ) as scraper:

            cefs = scraper.get_all_cefs()

            for cef in cefs:
                print(
                    f"Scraping {cef['name']} - {language}"
                )

                load_info = pipeline.run(
                    cef_resource(
                        cef,
                        language,
                        scraper,
                    )
                )

                print(load_info)


if __name__ == "__main__":
    main()