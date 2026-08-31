import json
import os
import re
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# ============================================================
# CONFIG
# ============================================================

SYMBOL = "2222"

COMPANY_URL = (
    "https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/company-profile-main/!ut/p/z1/jY_dbsIwDIWfhSeICWsaLgvVCqO_RBu0N8jLLIhW6JaG8vprudrQ_izfHPs78jGr2JZVJ-zMHp1pTlj3uqzEzgsE8IWETIbhHIr7lVw8QMZB-GzzFQCVez2QJ5MY1hCBYNV__PBDBfC3v7pBkkhAkQZFxn0PQPFb4JuIV-CXDArtNai_W-bR3Xgp-SoK1ByEEv56Ng0AJLCNpbY5W01svSeXoDmlzfGsE7Sv5EJyaOqWFRr1gWLqqM5xT0wNx017QacPsWmdopq0oxdWptmwanvV2BwtHsmRZeUw3LFy7Et_yicwkVxMh5nD55qeDF0-seNhYen9TK2LG401sbL_5O34uAWTd8ks9bq-k2A0-gCIxb_x/dz/d5/L0lHSklKSUtVS1VKQ2dwUkNTQ2lDbEVLSUtVU0ovWUJZRUFBSU1FQUFBRUVNQ0tJTUFHRUdPRU9FQkpGSkZCSk1OTkRETERMTkRISFBIUE5IQ0FvTUVBQSEhLzRKQ2lqSzJNWEhFSUpTWkNrbW9wektOTmJzWmJXYWptdDJNdHRWUlNxb3FRL1o3XzVBNjAySDgwTzBWQzQwNjBPNEdNTDgxRzU1L1o2XzVBNjAySDgwT0dGMkUwUUY5QlFERUcxMEs0L3ZpZXcvbm9ybWFsL2xhbmcvZW4vZ2xvYmFsL2h0dHA6JTAlMHRhZGF3dWwlMC9jb21wYW55U3ltYm9sLzIyMjI!/?locale=en"
)

OUTPUT_DIR = f"data/company_discovery/{SYMBOL}"

NETWORK_FILE = os.path.join(
    OUTPUT_DIR,
    "selenium_network_full.json"
)

ENDPOINT_FILE = os.path.join(
    OUTPUT_DIR,
    "endpoint_replay_candidates.json"
)


# ============================================================
# INTERESTING ENDPOINTS
# ============================================================

INTERESTING_ACTIONS = [
    "NJstatementsTabData",
    "NJforeginOwnerShip",
    "NJhistoricalBoardMembersWithDates",
    "NJhistoryOfMajorShareHolder",
    "NJpeerComparison",
    "NJgetCorporateAction",
    "NJgetAllEvents",
    "NJgetOptionsBySettlementDate",
    "NJupdatePriceBoxUrl",
    "RefreshTradeDetailsServlet",
    "TickerServlet",
]


# ============================================================
# HELPERS
# ============================================================

def extract_action(url):
    """
    Extract the meaningful IBM/WebSphere action from the ugly
    portal URL.

    Example:

        ...=NJstatementsTabData=/

    ->

        NJstatementsTabData
    """

    for action in INTERESTING_ACTIONS:
        if action in url:
            return action

    return None


def extract_parameters(url):
    parsed = urlparse(url)

    params = parse_qs(
        parsed.query,
        keep_blank_values=True
    )

    return {
        key: values[0] if len(values) == 1 else values
        for key, values in params.items()
    }


def is_interesting(url):
    return extract_action(url) is not None


# ============================================================
# CHROME
# ============================================================

options = Options()

# IMPORTANT:
# We need performance logging because this is how Selenium
# exposes Chrome's network events.
options.set_capability(
    "goog:loggingPrefs",
    {
        "performance": "ALL",
        "browser": "ALL",
    }
)

# Keep browser visible while debugging.
# DO NOT use headless yet.

driver = webdriver.Chrome(options=options)


# ============================================================
# START
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

print("=" * 70)
print("SAUDI EXCHANGE - FULL SELENIUM NETWORK CAPTURE")
print("=" * 70)
print()

print(f"Opening company {SYMBOL}...")
print(COMPANY_URL)
print()

driver.get(COMPANY_URL)

print("Page loaded.")
print()

# Give the company's JavaScript enough time to fire requests.
print("Waiting for dynamic requests...")
time.sleep(15)

print("Collecting Chrome performance logs...")
print()


# ============================================================
# COLLECT NETWORK EVENTS
# ============================================================

logs = driver.get_log("performance")

network_events = []

for entry in logs:

    try:
        message = json.loads(entry["message"])["message"]
    except Exception:
        continue

    method = message.get("method")
    params = message.get("params", {})

    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    if method == "Network.requestWillBeSent":

        request = params.get("request", {})

        url = request.get("url", "")

        if not url:
            continue

        event = {
            "timestamp": time.time(),
            "event": "request",
            "request_id": params.get("requestId"),
            "method": request.get("method"),
            "url": url,
            "resource_type": params.get("type"),
            "headers": request.get("headers", {}),
            "post_data": request.get("postData"),
        }

        network_events.append(event)

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    elif method == "Network.responseReceived":

        response = params.get("response", {})

        url = response.get("url", "")

        if not url:
            continue

        event = {
            "timestamp": time.time(),
            "event": "response",
            "request_id": params.get("requestId"),
            "status": response.get("status"),
            "status_text": response.get("statusText"),
            "url": url,
            "resource_type": params.get("type"),
            "mime_type": response.get("mimeType"),
            "headers": response.get("headers", {}),
        }

        network_events.append(event)


# ============================================================
# SAVE EVERYTHING
# ============================================================

with open(
    NETWORK_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        network_events,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# BUILD ENDPOINT INVENTORY
# ============================================================

requests = {}

for event in network_events:

    request_id = event.get("request_id")

    if not request_id:
        continue

    if request_id not in requests:
        requests[request_id] = {}

    if event["event"] == "request":

        requests[request_id]["request"] = event

    elif event["event"] == "response":

        requests[request_id]["response"] = event


candidates = []


for request_id, pair in requests.items():

    request = pair.get("request")

    if not request:
        continue

    url = request["url"]

    action = extract_action(url)

    if not action:
        continue

    response = pair.get("response", {})

    candidate = {
        "action": action,
        "request_id": request_id,
        "method": request.get("method"),
        "url": url,
        "parameters": extract_parameters(url),
        "resource_type": request.get("resource_type"),
        "status": response.get("status"),
        "mime_type": response.get("mime_type"),
        "request_headers": request.get("headers", {}),
    }

    candidates.append(candidate)


# Remove exact duplicates
unique = {}

for item in candidates:

    key = (
        item["action"],
        item["method"],
        item["url"],
    )

    unique[key] = item


candidates = list(unique.values())


# ============================================================
# SAVE ENDPOINT INVENTORY
# ============================================================

with open(
    ENDPOINT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        {
            "captured_at": datetime.now().isoformat(),
            "symbol": SYMBOL,
            "company_url": COMPANY_URL,
            "endpoints": candidates,
        },
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# PRINT RESULTS
# ============================================================

print("=" * 70)
print("CAPTURE COMPLETE")
print("=" * 70)
print()

print(f"Total Chrome network events: {len(network_events)}")
print(f"Interesting endpoints:        {len(candidates)}")
print()

for item in candidates:

    print("-" * 70)

    print(f"ACTION:      {item['action']}")
    print(f"METHOD:      {item['method']}")
    print(f"STATUS:      {item['status']}")
    print(f"TYPE:        {item['resource_type']}")
    print(f"MIME:        {item['mime_type']}")

    print()

    print("PARAMETERS:")

    for key, value in item["parameters"].items():
        print(f"  {key} = {value}")

    print()

    print("URL:")
    print(item["url"])

print()
print("=" * 70)
print("FILES")
print("=" * 70)

print(NETWORK_FILE)
print(ENDPOINT_FILE)

print()
print("Browser will remain open for inspection.")
print("Press ENTER to close it.")

input()

driver.quit()