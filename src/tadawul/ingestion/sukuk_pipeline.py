from __future__ import annotations

import json

import dlt

from tadawul.scraper.browser import TadawulBrowser
from tadawul.scraper.sukuk import SukukScraper


SUKUK_MARKET_URL = (
    "https://www.saudiexchange.sa/"
    "wps/portal/saudiexchange/ourmarkets/"
    "sukuk-market-watch/"
)

SUKUK_ENDPOINT = "NJgetSukukMarketDetails"


@dlt.resource(
    name="raw_corporate_sukuk",
    write_disposition="merge",
    primary_key=["symbol", "language"],
)
def corporate_sukuk_resource(
    sukuk: dict,
    language: str,
    scraper: SukukScraper,
):
    result = scraper.scrape(
        sukuk
    )

    result["language"] = language

    yield result


def main():
    pipeline = dlt.pipeline(
        pipeline_name="tadawul_corporate_sukuk",
        destination="postgres",
        dataset_name="raw_tadawul",
    )

    for language in ["en", "ar"]:
        with TadawulBrowser(
            headless=True,
        ) as browser:

            browser.set_locale(
                language
            )

            browser.open(
                SUKUK_MARKET_URL,
                wait_seconds=10,
            )

            response = browser.get_response_body(
                SUKUK_ENDPOINT
            )

            if not response:
                raise RuntimeError(
                    "Sukuk market response was not found"
                )

            data = json.loads(response)

            records = data.get(
                "data",
                [],
            )

            print(
                f"Total Sukuk/Bonds found: "
                f"{len(records)} - {language}"
            )

            if not records:
                raise RuntimeError(
                    f"No Sukuk/Bonds found for {language}"
                )

            corporate_sukuks = [
                sukuk
                for sukuk in records
                if sukuk.get("bondType") != "G"
            ]

            print(
                f"Corporate Sukuk/Bonds found: "
                f"{len(corporate_sukuks)} - {language}"
            )

            government_count = (
                len(records)
                - len(corporate_sukuks)
            )

            print(
                f"Government Sukuk/Bonds ignored: "
                f"{government_count} - {language}"
            )

            scraper = SukukScraper(
                browser=browser,
                language=language,
            )

            for sukuk in corporate_sukuks:
                print(
                    f"Scraping "
                    f"{sukuk.get('issuerName')} "
                    f"- {sukuk.get('symbol')} "
                    f"- {language}"
                )

                load_info = pipeline.run(
                    corporate_sukuk_resource(
                        sukuk,
                        language,
                        scraper,
                    )
                )

                print(load_info)


if __name__ == "__main__":
    main()