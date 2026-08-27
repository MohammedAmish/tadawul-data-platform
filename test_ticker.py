import json
import requests


URL = "https://www.saudiexchange.sa/tadawul.eportal.theme.helper/TickerServlet"

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en,ar;q=0.9",
    "Referer": "https://www.saudiexchange.sa/wps/portal/saudiexchange?locale=en",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
}


def main():
    session = requests.Session()

    # First establish a normal session with the main website.
    print("Opening Saudi Exchange...")
    home = session.get(
        "https://www.saudiexchange.sa/wps/portal/saudiexchange?locale=en",
        headers={
            "User-Agent": HEADERS["User-Agent"],
            "Accept-Language": HEADERS["Accept-Language"],
        },
        timeout=30,
    )

    print("Home status:", home.status_code)
    print("Cookies:", session.cookies.get_dict())

    # Now request the ticker endpoint using the same session.
    print("\nRequesting TickerServlet...")

    response = session.get(
        URL,
        headers=HEADERS,
        timeout=30,
    )

    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    print("Response length:", len(response.content))

    if response.status_code != 200:
        print("\nResponse preview:")
        print(response.text[:1000])
        return

    data = response.json()

    print("\nTop-level keys:", list(data.keys()))

    stock_data = data.get("stockData", [])

    print("Number of stocks:", len(stock_data))

    if stock_data:
        print("\nFirst stock:")
        print(json.dumps(stock_data[0], indent=2, ensure_ascii=False))

        print("\nFields:")
        print(list(stock_data[0].keys()))


if __name__ == "__main__":
    main()