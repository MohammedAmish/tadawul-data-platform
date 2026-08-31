from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests


BASE_URL = "https://www.saudiexchange.sa"

COMPANY_PAGE = (
    "/wps/portal/saudiexchange/hidden/company-profile-main/"
)

SYMBOL = "2222"

OUTPUT_DIR = Path("data/company_discovery") / SYMBOL
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_ajax_endpoints(html: str) -> list[dict]:
    endpoints = []

    # Find JavaScript variables such as:
    #
    # var getCorporateAction = 'p0/...';
    # var getAllEvents = 'p0/...';

    variable_pattern = re.compile(
        r"""
        (?:var\s+)?
        (?P<name>
            getCorporateAction|
            getAllEvents|
            getOptionsBySettlementDate
        )
        \s*=\s*
        ['"]
        (?P<url>[^'"]+)
        ['"]
        """,
        re.VERBOSE,
    )

    for match in variable_pattern.finditer(html):
        endpoints.append(
            {
                "name": match.group("name"),
                "url": match.group("url"),
                "source": "javascript_variable",
            }
        )

    # Direct $.ajax URLs.
    ajax_pattern = re.compile(
        r"""
        \$\.ajax\s*\(\s*\{
        (?P<body>.*?)
        \}\s*\)
        """,
        re.VERBOSE | re.DOTALL,
    )

    for match in ajax_pattern.finditer(html):
        body = match.group("body")

        url_match = re.search(
            r"""
            url\s*:\s*
            ['"]
            (?P<url>[^'"]+)
            ['"]
            """,
            body,
            re.VERBOSE,
        )

        if not url_match:
            continue

        url = url_match.group("url")

        data_match = re.search(
            r"""
            data\s*:\s*
            \{
                (?P<data>.*?)
            \}
            """,
            body,
            re.VERBOSE | re.DOTALL,
        )

        data = clean(data_match.group("data")) if data_match else None

        endpoints.append(
            {
                "name": None,
                "url": url,
                "data": data,
                "source": "jquery_ajax",
            }
        )

    return endpoints


def extract_named_functions(html: str) -> list[dict]:
    """
    Extract the company-specific functions we already identified.
    """

    names = [
        "populateAllEvent",
        "populateCorporateAction",
        "getOptionsBySettlementDate",
        "renderTabDataV2",
        "renderForeginOwnerShip",
        "renderBoardOFDirectortDates",
        "renderMajorShareHolder",
        "renderPeerComparison",
    ]

    results = []

    for name in names:
        pattern = re.compile(
            rf"function\s+{re.escape(name)}\s*\([^)]*\)"
        )

        for match in pattern.finditer(html):
            results.append(
                {
                    "function": name,
                    "declaration": clean(match.group(0)),
                }
            )

    return results


def main():
    url = (
        BASE_URL
        + COMPANY_PAGE
        + f"?companySymbol={SYMBOL}"
        + "&locale=en"
    )

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    print("=" * 70)
    print("Saudi Exchange - COMPANY ENDPOINT DISCOVERY")
    print("=" * 70)

    print(f"\nOpening company {SYMBOL}...")
    response = session.get(url, timeout=60)

    print(f"Status: {response.status_code}")
    print(f"Size:   {len(response.content):,} bytes")
    print(f"URL:    {response.url}")

    response.raise_for_status()

    html = response.text

    html_path = OUTPUT_DIR / "company_page.html"
    html_path.write_text(html, encoding="utf-8")

    endpoints = extract_ajax_endpoints(html)
    functions = extract_named_functions(html)

    inventory = {
        "company_symbol": SYMBOL,
        "page_url": response.url,
        "status_code": response.status_code,
        "response_size": len(response.content),
        "endpoints": endpoints,
        "company_functions": functions,
    }

    inventory_path = OUTPUT_DIR / "endpoint_inventory.json"

    inventory_path.write_text(
        json.dumps(
            inventory,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 70)
    print("DISCOVERY")
    print("=" * 70)

    print(f"AJAX endpoints discovered: {len(endpoints)}")
    print(f"Company functions found:    {len(functions)}")

    print("\nCompany functions:")

    for item in functions:
        print(
            f"  - {item['function']}: "
            f"{item['declaration']}"
        )

    print("\nEndpoints:")

    for item in endpoints:
        print(
            f"  - {item['name'] or '(direct AJAX)'}"
            f" -> {item['url']}"
        )

    print("\nSaved:")
    print(f"  {html_path}")
    print(f"  {inventory_path}")


if __name__ == "__main__":
    main()