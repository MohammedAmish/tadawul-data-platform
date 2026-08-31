from __future__ import annotations

import json
from pathlib import Path

from bs4 import BeautifulSoup

from tadawul.ingestion.browser import TadawulBrowser
from tadawul.ingestion.network_capture import NetworkCapture


class CompanyScraper:

    def __init__(
        self,
        output_dir: str = "data/raw/companies",
        headless: bool = False,
    ):
        self.output_dir = Path(output_dir)
        self.headless = headless

    def scrape(self, company: dict):
        symbol = str(company["company"])

        output = self.output_dir / symbol
        output.mkdir(parents=True, exist_ok=True)

        with TadawulBrowser(
            headless=self.headless
        ) as browser:

            print(f"Opening company {symbol}")

            current_url = browser.open(
                company["link"]
            )

            print("Current URL:")
            print(current_url)

            capture = NetworkCapture(
                browser.driver
            )

            requests = capture.collect(
                wait_seconds=5
            )

            self._save_network(
                output,
                requests
            )

            corporate_actions = [
                r
                for r in requests
                if "NJgetCorporateAction" in r["url"]
            ]

            print(
                f"Corporate action responses: "
                f"{len(corporate_actions)}"
            )

            for index, response in enumerate(
                corporate_actions
            ):
                body = response.get("body")

                if not body:
                    continue

                path = (
                    output /
                    f"corporate_actions_{index}.html"
                )

                path.write_text(
                    body,
                    encoding="utf-8"
                )

                print(
                    f"Saved {path}"
                )

                self._inspect_html(body)

    def _save_network(
        self,
        output: Path,
        requests: list[dict],
    ):
        path = output / "network.json"

        path.write_text(
            json.dumps(
                requests,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

    def _inspect_html(self, html: str):
        soup = BeautifulSoup(
            html,
            "lxml"
        )

        print(
            "HTML title:",
            soup.title.get_text(strip=True)
            if soup.title
            else None
        )

        tables = soup.find_all("table")

        print(
            "Tables:",
            len(tables)
        )