import json

from tadawul.scraper.mutual_fund import MutualFundScraper


def main():
    symbol = "011041"
    language = "ar"

    with MutualFundScraper(
        language=language,
        headless=True,
    ) as scraper:

        result = scraper.scrape(symbol)

    fund_name = result["fund_name"]

    output_path = (
        f"data/{fund_name}_{symbol}_{language}.json"
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

    print(f"Fund: {fund_name}")
    print(f"Symbol: {symbol}")
    print(f"Language: {language}")
    print(f"Result saved to: {output_path}")


if __name__ == "__main__":
    main()