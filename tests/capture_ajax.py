import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright


# Put the ACTUAL company page URL here.
# The safest approach is to copy it directly from your browser
# when company 2222 is open.
COMPANY_URL = os.environ.get(
    "COMPANY_URL",
    "https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/company-profile-main/!ut/p/z1/jY_dbsIwDIWfhSeICWsaLgvVCqO_RBu0N8jLLIhW6JaG8vprudrQ_izfHPs78jGr2JZVJ-zMHp1pTlj3uqzEzgsE8IWETIbhHIr7lVw8QMZB-GzzFQCVez2QJ5MY1hCBYNV__PBDBfC3v7pBkkhAkQZFxn0PQPFb4JuIV-CXDArtNai_W-bR3Xgp-SoK1ByEEv56Ng0AJLCNpbY5W01svSeXoDmlzfGsE7Sv5EJyaOqWFRr1gWLqqM5xT0wNx017QacPsWmdopq0oxdWptmwanvV2BwtHsmRZeUw3LFy7Et_yicwkVxMh5nD55qeDF0-seNhYen9TK2LG401sbL_5O34uAWTd8ks9bq-k2A0-gCIxb_x/dz/d5/L0lHSklKSUtVS1VKQ2dwUkNTQ2lDbEVLSUtVU0ovWUJZRUFBSU1FQUFBRUVNQ0tJTUFHRUdPRU9FQkpGSkZCSk1OTkRETERMTkRISFBIUE5IQ0FvTUVBQSEhLzRKQ2lqSzJNWEhFSUpTWkNrbW9wektOTmJzWmJXYWptdDJNdHRWUlNxb3FRL1o3XzVBNjAySDgwTzBWQzQwNjBPNEdNTDgxRzU1L1o2XzVBNjAySDgwT0dGMkUwUUY5QlFERUcxMEs0L3ZpZXcvbm9ybWFsL2xhbmcvZW4vZ2xvYmFsL2h0dHA6JTAlMHRhZGF3dWwlMC9jb21wYW55U3ltYm9sLzIyMjI!/?locale=en"
)

OUTPUT_DIR = Path("data/ajax_capture/2222")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


TARGETS = [
    "statementsTabData",
    "foreginOwnerShip",
    "historicalBoardMembersWithDates",
    "historyOfMajorShareHolder",
    "peerComparison",
    "getIndexDataURL",
]


async def main():

    print("=" * 70)
    print("Saudi Exchange Browser AJAX Capture")
    print("=" * 70)

    print(f"Opening:")
    print(COMPANY_URL)
    print()

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=False
        )

        context = await browser.new_context(
            locale="en-US",
            viewport={
                "width": 1440,
                "height": 900,
            },
        )

        page = await context.new_page()

        captured = []

        async def handle_response(response):

            url = response.url

            matched = None

            for target in TARGETS:
                if target in url:
                    matched = target
                    break

            if not matched:
                return

            request = response.request

            print()
            print("-" * 70)
            print("CAPTURED AJAX")
            print("-" * 70)
            print("NAME:", matched)
            print("STATUS:", response.status)
            print("METHOD:", request.method)
            print("URL:", url)

            try:
                headers = await request.all_headers()

                print("HEADERS:")
                for key, value in headers.items():
                    if key.lower() not in {
                        "cookie",
                        "authorization",
                    }:
                        print(f"  {key}: {value}")

            except Exception as exc:
                print("Could not read headers:", exc)
                headers = {}

            try:
                body = await response.body()

                filename = OUTPUT_DIR / f"{len(captured)+1:02d}_{matched}.html"

                filename.write_bytes(body)

                print("RESPONSE SIZE:", len(body))
                print("SAVED:", filename)

                captured.append({
                    "name": matched,
                    "status": response.status,
                    "method": request.method,
                    "url": url,
                    "request_headers": headers,
                    "response_size": len(body),
                    "response_file": str(filename),
                })

            except Exception as exc:
                print("Could not save response:", exc)

        page.on("response", handle_response)

        print("Navigating...")
        await page.goto(
            COMPANY_URL,
            wait_until="domcontentloaded",
            timeout=120000,
        )

        print()
        print("Page loaded.")
        print()
        print("Waiting for AJAX activity...")
        print("If necessary, interact with the page manually.")
        print("The browser will remain open for 60 seconds.")
        print()

        await page.wait_for_timeout(60_000)

        metadata_file = OUTPUT_DIR / "capture.json"

        metadata_file.write_text(
            json.dumps(
                captured,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print()
        print("=" * 70)
        print("CAPTURE COMPLETE")
        print("=" * 70)
        print(f"Captured: {len(captured)} AJAX requests")
        print(f"Metadata: {metadata_file}")
        print()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())