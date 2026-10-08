import json

from tadawul.scraper.browser import TadawulBrowser
from tadawul.scraper.sukuk import SukukScraper


SUKUK_MARKET_URL = (
    "https://www.saudiexchange.sa/"
    "wps/portal/saudiexchange/ourmarkets/"
    "sukuk-market-watch/"
)

SUKUK_ENDPOINT = "NJgetSukukMarketDetails"
TEST_SYMBOL = "5027"


def main():
    print("=" * 60)
    print("CORPORATE SUKUK/BONDS SCRAPER")
    print("=" * 60)

    language = "en"

    with TadawulBrowser(headless=True) as browser:
        browser.set_locale(language)

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

        records = data.get("data", [])

        print(
            f"Total Sukuk/Bonds found: {len(records)}"
        )

        record = next(
            (
                record
                for record in records
                if record.get("symbol") == TEST_SYMBOL
            ),
            None,
        )

        if record is None:
            raise RuntimeError(
                f"Sukuk/Bond {TEST_SYMBOL} was not found"
            )

        print()
        print(f"Testing symbol: {record.get('symbol')}")
        print(f"Issuer: {record.get('issuerName')}")
        print(f"Sector: {record.get('sectorName')}")

        scraper = SukukScraper(
            browser=browser,
            language=language,
        )

        result = scraper.scrape(record)

    issuer_name = result["issuer_name"]
    symbol = result["symbol"]

    output_path = (
        f"data/{issuer_name}_{symbol}_{language}.json"
    )

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

    print()
    print("=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)
    print(f"Issuer: {issuer_name}")
    print(f"Symbol: {symbol}")
    print(f"Language: {language}")
    print(f"Result saved to: {output_path}")


if __name__ == "__main__":
    main()