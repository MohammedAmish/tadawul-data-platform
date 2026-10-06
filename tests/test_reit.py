import json

from tadawul.scraper.reit import ReitScraper


def main():
    language = "ar"

    with ReitScraper(
        language=language,
        headless=True,
    ) as scraper:

        reits = scraper.get_all_reits()

        print(f"Found {len(reits)} REITs")

        first_reit = reits[0]

        result = scraper.scrape(
            first_reit["url"]
        )

    reit_name = result["reit_name"]
    symbol = result["symbol"]

    output_path = (
        f"data/{reit_name}_{symbol}_{language}.json"
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

    print(f"REIT: {reit_name}")
    print(f"Symbol: {symbol}")
    print(f"Language: {language}")
    print(f"Result saved to: {output_path}")


if __name__ == "__main__":
    main()