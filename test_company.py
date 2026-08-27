import json
from pathlib import Path

import requests


# ============================================================
# Configuration
# ============================================================

BASE_URL = "https://www.saudiexchange.sa"

TICKER_DATA_FILE = Path("data/tickerData.json")

# Company we want to test
COMPANY_SYMBOL = "2222"

# Output HTML
OUTPUT_FILE = Path(f"company_{COMPANY_SYMBOL}.html")


# ============================================================
# Load ticker data
# ============================================================

def load_ticker_data():
    """
    Load ticker data from data/ticker_data.json.

    The JSON file contains an array like:

    [
        {
            "company": "2222",
            "companyDisplay": "SAUDI ARAMCO",
            "link": "...",
            ...
        }
    ]
    """

    if not TICKER_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Ticker data file not found: {TICKER_DATA_FILE}"
        )

    print(f"Loading ticker data from: {TICKER_DATA_FILE}")

    with open(TICKER_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            "ticker_data.json must contain a JSON array."
        )

    print(f"Loaded {len(data)} ticker records.")

    return data


# ============================================================
# Build ticker lookup
# ============================================================

def build_ticker_lookup(ticker_data):
    """
    Convert the ticker list into a dictionary keyed by company symbol.

    Example:

        {
            "2222": {...},
            "2030": {...},
            "4700": {...}
        }
    """

    lookup = {}

    for item in ticker_data:
        company = item.get("company")

        if company is None:
            continue

        company = str(company)

        lookup[company] = item

    return lookup


# ============================================================
# Get company information
# ============================================================

def get_company(ticker_lookup, company_symbol):
    """
    Find a company by its Tadawul company symbol.
    """

    company_symbol = str(company_symbol)

    company = ticker_lookup.get(company_symbol)

    if company is None:
        raise ValueError(
            f"Company {company_symbol} was not found in "
            f"{TICKER_DATA_FILE}"
        )

    return company


# ============================================================
# Create full company URL
# ============================================================

def build_company_url(company):
    """
    Convert the relative link from ticker_data.json into
    a complete Saudi Exchange URL.
    """

    link = company.get("link")

    if not link:
        raise ValueError(
            f"No 'link' found for company {company.get('company')}"
        )

    # Already absolute
    if link.startswith("http://") or link.startswith("https://"):
        return link

    # Relative URL
    if link.startswith("/"):
        return BASE_URL + link

    # Unexpected format
    return BASE_URL + "/" + link


# ============================================================
# Main
# ============================================================

def main():

    # --------------------------------------------------------
    # Load ticker data
    # --------------------------------------------------------

    print("Loading ticker data...")

    ticker_data = load_ticker_data()

    ticker_lookup = build_ticker_lookup(ticker_data)

    print(f"Ticker lookup contains {len(ticker_lookup)} companies.")

    # --------------------------------------------------------
    # Find company
    # --------------------------------------------------------

    print()
    print(f"Looking for company {COMPANY_SYMBOL}...")

    company = get_company(
        ticker_lookup,
        COMPANY_SYMBOL
    )

    print()
    print("Company found:")
    print(f"  Symbol:       {company.get('company')}")
    print(f"  Display name: {company.get('companyDisplay')}")
    print(f"  Price:        {company.get('price')}")
    print(f"  Change:       {company.get('change')}")
    print(f"  Change %:     {company.get('changePercent')}")

    # --------------------------------------------------------
    # Get URL from tickerData
    # --------------------------------------------------------

    company_url = build_company_url(company)

    print()
    print("Company URL from tickerData:")
    print(company_url)

    # --------------------------------------------------------
    # Create HTTP session
    # --------------------------------------------------------

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,image/webp,"
            "image/apng,*/*;q=0.8,"
            "application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Language": "en,ar;q=0.9",
        "Cache-Control": "max-age=0",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    })

    # --------------------------------------------------------
    # Open Saudi Exchange homepage first
    # --------------------------------------------------------

    print()
    print("Opening Saudi Exchange...")

    home_url = f"{BASE_URL}/wps/portal/saudiexchange?locale=en"

    home_response = session.get(
        home_url,
        timeout=30
    )

    print(f"Home status: {home_response.status_code}")
    print(f"Home response length: {len(home_response.text)}")

    print()
    print("Cookies:")
    print(session.cookies.get_dict())

    # --------------------------------------------------------
    # Request company page
    # --------------------------------------------------------

    print()
    print(f"Requesting company {COMPANY_SYMBOL}...")

    response = session.get(
        company_url,
        headers={
            "Referer": home_url,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        },
        timeout=30
    )

    print()
    print("Final URL:")
    print(response.url)

    print()
    print(f"Company status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Response length: {len(response.text)}")

    # --------------------------------------------------------
    # Save HTML
    # --------------------------------------------------------

    OUTPUT_FILE.write_text(
        response.text,
        encoding="utf-8"
    )

    print()
    print(f"Saved HTML to: {OUTPUT_FILE}")

    # --------------------------------------------------------
    # Basic checks
    # --------------------------------------------------------

    html = response.text

    print()
    print("Content checks:")

    checks = {
        COMPANY_SYMBOL: COMPANY_SYMBOL in html,
        company.get("companyDisplay", ""): (
            company.get("companyDisplay", "") in html
        ),
        "Financials": "Financials" in html,
        "Shareholding": "Shareholding" in html,
        "Peer Comparison": "Peer Comparison" in html,
        "Announcements": "Announcements" in html,
    }

    for name, found in checks.items():
        print(
            f"{name}: {'FOUND' if found else 'NOT FOUND'}"
        )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()