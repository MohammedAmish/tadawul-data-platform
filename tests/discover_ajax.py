from pathlib import Path
import requests
import json


# ============================================================
# Configuration
# ============================================================

SYMBOL = "2222"

# Exact company-page URL that initiated the AJAX request.
REFERER_URL = (
    "https://www.saudiexchange.sa"
    "/wps/portal/saudiexchange/hidden/company-profile-main/"
    "!ut/p/z1/jY_dbsIwDIWfhSeICWsaLgvVCqO_RBu0N8jLLIhW6JaG8vprudrQ_"
    "izfHPs78jGr2JZVJ-zMHp1pTlj3uqzEzgsE8IWETIbhHIr7lVw8QMZB-GzzF"
    "QCVez2QJ5MY1hCBYNV__PBDBfC3v7pBkkhAkQZFxn0PQPFb4JuIV-CXDArt"
    "Nai_W-bR3Xgp-SoK1ByEEv56Ng0AJLCNpbY5W01svSeXoDmlzfGsE7Sv5EJ"
    "yaOqWFRr1gWLqqM5xT0wNx017QacPsWmdopq0oxdWptmwanvV2BwtHsmRZe"
    "Uw3LFy7Et_yicwkVxMh5nD55qeDF0-seNhYen9TK2LG401sbL_5O34uAWTd"
    "8ks9bq-k2A0-gCIxb_x/dz/d5/L0lHSklKSUtVS1VKQ2dwUkNTQ2lDbEVL"
    "SUtVU0ovWUJZRUFBSU1FQUFBRUVNQ0tJTUFHRUdPRU9FQkpGSkZCSk1OTk"
    "RETERMTkRISFBIUE5IQ0FvTUVBQSEhLzRKQ2lqSzJNWEhFSUpTWkNrbW9w"
    "ektOTmJzWmJXYWptdDJNdHRWUlNxb3FRL1o3XzVBNjAySDgwTzBWQzQwNj"
    "BPNEdNTDgxRzU1L1o2XzVBNjAySDgwT0dGMkUwUUY5QlFERUcxMEs0L3Zp"
    "ZXcvbm9ybWFsL2xhbmcvaW4vZ2xvYmFsL2h0dHA6JTAlMHRhZGF3dWwlMC9j"
    "b21wYW55U3ltYm9sLzIyMjI!/?locale=en"
)


# Exact dynamic AJAX URL captured from Chrome.
#
# IMPORTANT:
# We will modify ONLY the query parameters.
# The long /wps/.../p0/... path remains unchanged.
#
AJAX_BASE_URL = (
    "https://www.saudiexchange.sa"
    "/wps/portal/saudiexchange/hidden/company-profile-main/"
    "!ut/p/z1/jZFPU4MwEMU_DUdnt5EE9Ia1jX9ASmMFcnFCZRAnJIyD7fTbG_"
    "VinZa6t535vX1vd0FCAdKoTduoobVGadeXkj3TiCG5CTHlczLDbH5xlV3P-"
    "ATvfcj3ARQL6oBFch7jEjkykP_R45GKzBEKDMKcTQzMDPxN3H19LAzdTU31w8syU8v1wwkpK8hOMgUA-oskdg!!/"
    "p0/IZ7_5A602H80O0VC4060O4GML81G57="
    "CZ6_5A602H80OGF2E0QF9BQDEG10K4="
    "NJstatementsTabData=/"
)


# ============================================================
# Current Chrome cookies
# ============================================================

COOKIE_STRING = r"""
BIGipServerSaudiExchange.sa.app~SaudiExchange.sa_pool=!SerMmr+UM+L3S+l8Q2uV0kKUCXWosfllB84zZA5RlhR7hfxeuOOq57DNip4KiEWy+frQhW847r7nJyA=; com.ibm.wps.state.preprocessors.locale.LanguageCookie=en; JSESSIONID=!wu3QQ/L04jahHZpSt8odDubmCbPRCarHCPjyk7fq/pQ9VC1UVqiCohaoz9rrOlDX81wSJXhJc8z8BrHAQ+d1LZVraYDuIC2DBNNk; TS0165c9d2=0102d17fad054576fc46b512d605fd348a7c116c068db9a47a4a46fd4408679301436bafa04f9d9ad1c25e0a583300c7da704daf356ff740a930eb8cde016dd29b1076e1b1668f10dcc629358499eaa11c33da09a92eb4dda34f283f96d67135826cccd857; marqueePosition_ltr=-37418.672640000106
""".strip()


# ============================================================
# Statement types
# ============================================================

STATEMENT_TYPES = {
    0: "balance_sheet",
    1: "income_statement",
    2: "cash_flow",
    4: "xbrl",
    5: "report_statement",
    6: "financial_statements_and_reports",
}


# ============================================================
# Output
# ============================================================

OUTPUT_DIR = Path("data/ajax") / SYMBOL
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Helpers
# ============================================================

def parse_cookie_string(cookie_string: str) -> dict:
    cookies = {}

    for part in cookie_string.split(";"):
        part = part.strip()

        if not part or "=" not in part:
            continue

        name, value = part.split("=", 1)
        cookies[name.strip()] = value.strip()

    return cookies


def is_request_rejected(response: requests.Response) -> bool:
    text = response.text.lower()

    markers = [
        "request rejected",
        "support id:",
        "the requested url was rejected",
    ]

    return any(marker in text for marker in markers)


def contains_financial_content(response: requests.Response) -> bool:
    text = response.text.lower()

    indicators = [
        "financial",
        "statement",
        "revenue",
        "assets",
        "liabilities",
        "equity",
        "income",
        "cash flow",
    ]

    return any(x in text for x in indicators)


def save_response(
    response: requests.Response,
    statement_type: int,
    name: str,
):
    html_file = OUTPUT_DIR / f"statement_{statement_type}_{name}.html"
    json_file = OUTPUT_DIR / f"statement_{statement_type}_{name}.json"

    html_file.write_bytes(response.content)

    metadata = {
        "symbol": SYMBOL,
        "statement_type": statement_type,
        "statement_name": name,
        "url": response.url,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type"),
        "size_bytes": len(response.content),
        "successful": (
            response.status_code == 200
            and not is_request_rejected(response)
        ),
        "financial_content_detected": contains_financial_content(response),
    }

    json_file.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    return html_file, json_file


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("Saudi Exchange - FINANCIAL AJAX TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Cookies
    # --------------------------------------------------------

    cookies = parse_cookie_string(COOKIE_STRING)

    print()
    print(f"Loaded {len(cookies)} cookies:")

    for name in cookies:
        print(f"  - {name}")

    # --------------------------------------------------------
    # Session
    # --------------------------------------------------------

    session = requests.Session()

    session.headers.update({
        "Accept": "text/html, */*; q=0.01",
        "Accept-Language": "en,ar;q=0.9",
        "DNT": "1",
        "Priority": "u=1, i",
        "Referer": REFERER_URL,
        "Sec-CH-UA": (
            '"Not=A?Brand";v="99", '
            '"Google Chrome";v="151", '
            '"Chromium";v="151"'
        ),
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
    })

    session.cookies.update(cookies)

    # --------------------------------------------------------
    # Establish company-page session
    # --------------------------------------------------------

    print()
    print("Opening company page to establish session...")

    try:
        page = session.get(
            REFERER_URL,
            timeout=30,
        )

    except requests.RequestException as exc:
        print()
        print("❌ Company page request failed:")
        print(exc)
        return

    print(f"Company page status: {page.status_code}")
    print(f"Company page size:   {len(page.content):,} bytes")

    if page.status_code != 200:
        print()
        print("❌ Cannot continue because company page did not return 200.")
        return

    # --------------------------------------------------------
    # Test every statement type
    # --------------------------------------------------------

    results = []

    for statement_type, name in STATEMENT_TYPES.items():

        print()
        print("=" * 70)
        print(
            f"STATEMENT TYPE {statement_type}: {name}"
        )
        print("=" * 70)

        params = {
            "statementType": statement_type,
            "reportType": 0,
            "requestLocale": "en",
            "symbol": SYMBOL,
        }

        print()
        print("Parameters:")
        print(params)

        try:

            response = session.get(
                AJAX_BASE_URL,
                params=params,
                timeout=30,
            )

        except requests.RequestException as exc:

            print()
            print("❌ Request failed:")
            print(exc)

            results.append({
                "statement_type": statement_type,
                "name": name,
                "success": False,
                "error": str(exc),
            })

            continue

        # ----------------------------------------------------
        # Response information
        # ----------------------------------------------------

        print()
        print("Response:")
        print(f"  Status:       {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type')}")
        print(f"  Size:         {len(response.content):,} bytes")

        # ----------------------------------------------------
        # Rejection check
        # ----------------------------------------------------

        if is_request_rejected(response):

            print()
            print("❌ REQUEST REJECTED")

            html_file, json_file = save_response(
                response,
                statement_type,
                name,
            )

            print(f"  Saved: {html_file}")

            results.append({
                "statement_type": statement_type,
                "name": name,
                "success": False,
                "rejected": True,
                "status_code": response.status_code,
                "size_bytes": len(response.content),
            })

            continue

        # ----------------------------------------------------
        # Successful response
        # ----------------------------------------------------

        if response.status_code == 200:

            has_financial_content = contains_financial_content(response)

            if has_financial_content:
                print("  ✓ Financial content detected")
            else:
                print("  ⚠ No obvious financial content detected")

            html_file, json_file = save_response(
                response,
                statement_type,
                name,
            )

            print()
            print("✅ SUCCESS")
            print(f"  HTML: {html_file}")
            print(f"  JSON: {json_file}")

            results.append({
                "statement_type": statement_type,
                "name": name,
                "success": True,
                "status_code": response.status_code,
                "size_bytes": len(response.content),
                "financial_content_detected": has_financial_content,
            })

        else:

            print(f"⚠ HTTP {response.status_code}")

            html_file, json_file = save_response(
                response,
                statement_type,
                name,
            )

            results.append({
                "statement_type": statement_type,
                "name": name,
                "success": False,
                "status_code": response.status_code,
                "size_bytes": len(response.content),
            })

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    successful = 0

    for result in results:

        status = "✅" if result.get("success") else "❌"

        print(
            f"{status} "
            f"{result['statement_type']:>2} "
            f"{result['name']:<35} "
            f"{result.get('size_bytes', 0):>10,} bytes"
        )

        if result.get("success"):
            successful += 1

    # --------------------------------------------------------
    # Save combined test results
    # --------------------------------------------------------

    summary_file = OUTPUT_DIR / "financial_statement_test_summary.json"

    summary_file.write_text(
        json.dumps(
            {
                "symbol": SYMBOL,
                "successful_count": successful,
                "total_count": len(results),
                "results": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(f"Summary saved:")
    print(f"  {summary_file}")

    print()
    print("=" * 70)
    print(f"Completed: {successful}/{len(results)} successful")
    print("=" * 70)


if __name__ == "__main__":
    main()