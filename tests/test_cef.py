import json

from tadawul.scraper.cef import CefScraper


def main():
    language = "ar"

    with CefScraper(
        language=language,
        headless=True,
    ) as scraper:

        cefs = scraper.get_all_cefs()

        print(f"Found {len(cefs)} CEFs")

        first_cef = cefs[2]

        result = scraper.scrape(
            first_cef["url"]
        )

    cef_name = result["cef_name"]
    symbol = result["symbol"]

    output_path = (
        f"data/{cef_name}_{symbol}_{language}.json"
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

    print(f"CEF: {cef_name}")
    print(f"Symbol: {symbol}")
    print(f"Language: {language}")
    print(f"Result saved to: {output_path}")


if __name__ == "__main__":
    main()