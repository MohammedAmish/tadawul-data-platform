from __future__ import annotations

import re
from pathlib import Path

from tadawul.scraper.browser import TadawulBrowser
from tadawul.scraper.servlet import TadawulServlet


OUTPUT_FILE = (
    Path(__file__).resolve().parent
    / "discovered_company_symbols.py"
)


def get_ticker_symbols(browser: TadawulBrowser) -> list[str]:
    ticker_data = browser.get_ticker_data()

    symbols = re.findall(
        r'company:\s*"([^"]+)"',
        ticker_data,
    )

    return list(dict.fromkeys(symbols))


def discover_company_symbols():
    servlet = TadawulServlet()

    servlet_companies = servlet.fetch()

    servlet_by_symbol = {
        company["symbol"]: company
        for company in servlet_companies
        if company.get("symbol")
    }

    with TadawulBrowser(headless=True) as browser:
        browser.open(
            browser.BASE_URL,
            wait_seconds=5,
        )

        ticker_symbols = get_ticker_symbols(browser)

    main_market = []
    nomu = []

    for symbol in ticker_symbols:
        company = servlet_by_symbol.get(symbol)

        if not company:
            continue

        market_type = company.get("market_type")

        if market_type == "M":
            main_market.append(symbol)
        elif market_type == "S":
            nomu.append(symbol)

    return main_market, nomu


def save_symbols(main_market: list[str], nomu: list[str]):
    content = (
        "MAIN_MARKET_SYMBOLS = [\n"
        + "".join(f'    "{symbol}",\n' for symbol in main_market)
        + "]\n\n"
        + "NOMU_SYMBOLS = [\n"
        + "".join(f'    "{symbol}",\n' for symbol in nomu)
        + "]\n"
    )

    OUTPUT_FILE.write_text(
        content,
        encoding="utf-8",
    )


def main():
    main_market, nomu = discover_company_symbols()
    save_symbols(main_market, nomu)


if __name__ == "__main__":
    main()