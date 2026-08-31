from __future__ import annotations

import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class TadawulBrowser:
    BASE_URL = "https://www.saudiexchange.sa"

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = self._create_driver()

    def _create_driver(self):
        options = Options()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        options.set_capability(
            "goog:loggingPrefs",
            {
                "performance": "ALL",
                "browser": "ALL",
            },
        )

        driver = webdriver.Chrome(options=options)

        driver.execute_cdp_cmd(
            "Network.enable",
            {}
        )

        return driver

    def open(self, relative_url: str):
        if relative_url.startswith("http"):
            url = relative_url
        else:
            url = self.BASE_URL + relative_url

        self.driver.get(url)

        # Give the WebSphere page time to initialize its JS.
        time.sleep(8)

        return self.driver.current_url

    def execute_async(self, script: str, *args):
        return self.driver.execute_async_script(script, *args)

    def execute(self, script: str, *args):
        return self.driver.execute_script(script, *args)

    def close(self):
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()