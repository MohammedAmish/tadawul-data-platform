from __future__ import annotations

import requests


class TadawulServlet:
    BASE_URL = "https://www.saudiexchange.sa"

    ENDPOINT = (
        "/tadawul.eportal.theme.helper/"
        "ThemeSearchUtilityServlet"
    )

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept": (
                    "application/json, "
                    "text/javascript, */*; q=0.01"
                ),
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/152.0.0.0 Safari/537.36"
                ),
                "X-Requested-With": "XMLHttpRequest",
            }
        )

    def fetch(self):
        url = self.BASE_URL + self.ENDPOINT

        response = self.session.get(
            url,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()