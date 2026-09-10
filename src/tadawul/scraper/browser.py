from __future__ import annotations

import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class TadawulBrowser:
    BASE_URL = "https://www.saudiexchange.sa"

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = self._create_driver()

    def _create_driver(self):
        options = Options()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/152.0.0.0 Safari/537.36"
        )

        options.set_capability(
            "goog:loggingPrefs",
            {"performance": "ALL"},
        )

        return webdriver.Chrome(options=options)

    def open(self, url: str, wait_seconds: int = 10):
        self.driver.get(url)
        time.sleep(wait_seconds)
        return self.driver

    def close(self):
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self.driver

    def __exit__(self, exc_type, exc, tb):
        self.close()