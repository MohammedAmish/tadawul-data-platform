import json

from tadawul.scraper.company import CompanyScraper


def main():
    symbol = "2222"
    language = "en"

    scraper = CompanyScraper(
        language=language,
        headless=False,
    )

    result = scraper.scrape(symbol)

    company_name = result["company_name"]

    output_path = (
        f"data/{company_name}_{symbol}_{language}.json"
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

    print(f"Company: {company_name}")
    print(f"Symbol: {symbol}")
    print(f"Language: {language}")
    print(f"Result saved to: {output_path}")


if __name__ == "__main__":
    main()