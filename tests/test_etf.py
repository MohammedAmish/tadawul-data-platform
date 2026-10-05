import json

from tadawul.scraper.etf import EtfScraper


def main():
    language = "ar"

    with EtfScraper(
        language=language,
        headless=True,
    ) as scraper:

        etfs = scraper.get_all_etfs()

        print(f"Found {len(etfs)} ETFs")

        first_etf = etfs[0]

        result = scraper.scrape(
            first_etf["url"]
        )

    etf_name = result["etf_name"]
    symbol = result["symbol"]

    output_path = (
        f"data/{etf_name}_{symbol}_{language}.json"
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

    print(f"ETF: {etf_name}")
    print(f"Symbol: {symbol}")
    print(f"Language: {language}")
    print(f"Result saved to: {output_path}")


if __name__ == "__main__":
    main()