from pathlib import Path
import requests
import json
import re
from urllib.parse import urljoin


# ============================================================
# Configuration
# ============================================================

SYMBOL = "2222"

COMPANY_URL = (
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


# ============================================================
# CURRENT COOKIES FROM CHROME
# ============================================================

COOKIE_STRING = r"""
BIGipServerSaudiExchange.sa.app~SaudiExchange.sa_pool=!SerMmr+UM+L3S+l8Q2uV0kKUCXWosfllB84zZA5RlhR7hfxeuOOq57DNip4KiEWy+frQhW847r7nJyA=; com.ibm.wps.state.preprocessors.locale.LanguageCookie=en; JSESSIONID=!wu3QQ/L04jahHZpSt8odDubmCbPRCarHCPjyk7fq/pQ9VC1UVqiCohaoz9rrOlDX81wSJXhJc8z8BrHAQ+d1LZVraYDuIC2DBNNk; TS0165c9d2=0102d17fad054576fc46b512d605fd348a7c116c068db9a47a4a46fd4408679301436bafa04f9d9ad1c25e0a583300c7da704daf356ff740a930eb8cde016dd29b1076e1b1668f10dcc629358499eaa11c33da09a92eb4dda34f283f96d67135826cccd857; marqueePosition_ltr=-37418.672640000106
""".strip()


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = Path("data/company_discovery") / SYMBOL
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HTML_FILE = OUTPUT_DIR / "company_page.html"
DISCOVERY_FILE = OUTPUT_DIR / "discovery.json"


# ============================================================
# HELPERS
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


def unique(values):

    result = []

    seen = set()

    for value in values:

        if value not in seen:

            seen.add(value)
            result.append(value)

    return result


def extract_links(html):

    pattern = re.compile(
        r'''(?:href|src)\s*=\s*["']([^"']+)["']''',
        re.IGNORECASE,
    )

    return unique(pattern.findall(html))


def extract_forms(html):

    forms = []

    pattern = re.compile(
        r"<form\b([^>]*)>(.*?)</form>",
        re.IGNORECASE | re.DOTALL,
    )

    for match in pattern.finditer(html):

        attributes = match.group(1)
        body = match.group(2)

        action_match = re.search(
            r'action\s*=\s*["\']([^"\']*)["\']',
            attributes,
            re.IGNORECASE,
        )

        method_match = re.search(
            r'method\s*=\s*["\']([^"\']*)["\']',
            attributes,
            re.IGNORECASE,
        )

        forms.append({
            "action": action_match.group(1)
            if action_match else "",

            "method": method_match.group(1)
            if method_match else "GET",

            "size": len(body),
        })

    return forms


def extract_matching_lines(html):

    keywords = [
        "ajax",
        "$.ajax",
        "$.get",
        "$.post",
        "fetch(",
        "xmlhttprequest",
        "renderTabData",
        "renderTabDataV2",
        "TabData",
        "statementType",
        "requestLocale",
        "contenthandler",
        "companySymbol",
        "companysymbol",
        "symbol",
        "/wps/",
    ]

    lines = html.splitlines()

    matches = []

    for number, line in enumerate(lines, start=1):

        lower = line.lower()

        found = []

        for keyword in keywords:

            if keyword.lower() in lower:

                found.append(keyword)

        if found:

            matches.append({
                "line": number,
                "keywords": found,
                "text": line.strip()[:2000],
            })

    return matches


def extract_ajax_candidates(html):

    candidates = []

    patterns = [

        # URLs in quotes
        r'''["']([^"']*(?:ajax|TabData|tabData|contenthandler)[^"']*)["']''',

        # URLs containing statementType
        r'''["']([^"']*statementType[^"']*)["']''',

        # URLs containing companySymbol
        r'''["']([^"']*companySymbol[^"']*)["']''',

        # URLs containing symbol
        r'''["']([^"']*[?&]symbol=[^"']*)["']''',
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            html,
            re.IGNORECASE,
        )

        candidates.extend(matches)

    return unique(candidates)


def extract_portlets(html):

    names = []

    patterns = [

        r'id=["\']([^"\']*(?:company|financial|share|announcement|profile)[^"\']*)["\']',

        r'class=["\']([^"\']*(?:portlet|tab)[^"\']*)["\']',

        r'##\s*([A-Za-z0-9]+)',
    ]

    for pattern in patterns:

        names.extend(
            re.findall(
                pattern,
                html,
                re.IGNORECASE,
            )
        )

    return unique(names)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("Saudi Exchange - COMPLETE COMPANY PAGE DISCOVERY")
    print("=" * 70)

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

        "Accept":
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,*/*;q=0.8",

        "Accept-Language":
            "en,ar;q=0.9",

        "DNT":
            "1",

        "User-Agent":
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
    })

    session.cookies.update(cookies)

    # --------------------------------------------------------
    # Download complete page
    # --------------------------------------------------------

    print()
    print("Downloading COMPLETE company page...")

    try:

        response = session.get(
            COMPANY_URL,
            timeout=60,
        )

    except requests.RequestException as exc:

        print()
        print("ERROR:")
        print(exc)

        return

    print()
    print("=" * 70)
    print("RESPONSE")
    print("=" * 70)

    print(f"Status:       {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Size:         {len(response.content):,} bytes")
    print(f"Final URL:    {response.url}")

    if response.status_code != 200:

        print()
        print("❌ Company page request failed.")

        HTML_FILE.write_bytes(response.content)

        return

    html = response.text

    # --------------------------------------------------------
    # Save raw HTML
    # --------------------------------------------------------

    HTML_FILE.write_bytes(response.content)

    print()
    print("Saved complete HTML:")
    print(f"  {HTML_FILE}")

    # --------------------------------------------------------
    # Discover resources
    # --------------------------------------------------------

    links = extract_links(html)

    forms = extract_forms(html)

    matching_lines = extract_matching_lines(html)

    ajax_candidates = extract_ajax_candidates(html)

    portlets = extract_portlets(html)

    # --------------------------------------------------------
    # Separate JavaScript
    # --------------------------------------------------------

    scripts = [
        x
        for x in links
        if ".js" in x.lower()
    ]

    # --------------------------------------------------------
    # Separate interesting URLs
    # --------------------------------------------------------

    interesting_links = []

    interesting_keywords = [

        "ajax",
        "tab",
        "financial",
        "statement",
        "announcement",
        "corporate",
        "shareholding",
        "dividend",
        "peer",
        "profile",
        "contenthandler",
        "company",
        "historical",
    ]

    for link in links:

        lower = link.lower()

        if any(
            keyword in lower
            for keyword in interesting_keywords
        ):

            interesting_links.append(link)

    # --------------------------------------------------------
    # Build discovery document
    # --------------------------------------------------------

    discovery = {

        "symbol": SYMBOL,

        "url": response.url,

        "status_code":
            response.status_code,

        "content_type":
            response.headers.get("content-type"),

        "size_bytes":
            len(response.content),

        "links": links,

        "interesting_links":
            unique(interesting_links),

        "javascript_files":
            scripts,

        "forms":
            forms,

        "ajax_candidates":
            ajax_candidates,

        "portlet_candidates":
            portlets,

        "matching_source_lines":
            matching_lines,
    }

    DISCOVERY_FILE.write_text(
        json.dumps(
            discovery,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("DISCOVERY SUMMARY")
    print("=" * 70)

    print()
    print(f"Total links:              {len(links)}")
    print(f"Interesting links:        {len(interesting_links)}")
    print(f"JavaScript files:         {len(scripts)}")
    print(f"Forms:                    {len(forms)}")
    print(f"AJAX candidates:          {len(ajax_candidates)}")
    print(f"Portlet candidates:       {len(portlets)}")
    print(f"Matching source lines:    {len(matching_lines)}")

    print()
    print("Saved:")
    print(f"  {HTML_FILE}")
    print(f"  {DISCOVERY_FILE}")

    # --------------------------------------------------------
    # Show interesting candidates
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("AJAX / DYNAMIC CONTENT CANDIDATES")
    print("=" * 70)

    for item in ajax_candidates[:100]:

        print()
        print(item)

    print()
    print("=" * 70)
    print("IMPORTANT SOURCE LINES")
    print("=" * 70)

    for item in matching_lines[:100]:

        print()
        print(
            f"LINE {item['line']} "
            f"[{', '.join(item['keywords'])}]"
        )

        print(item["text"][:1000])


if __name__ == "__main__":
    main()