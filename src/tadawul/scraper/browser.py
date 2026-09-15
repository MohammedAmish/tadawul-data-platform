from __future__ import annotations

import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tadawul.scraper.servlet import TadawulServlet


class TadawulBrowser:
    BASE_URL = "https://www.saudiexchange.sa"

    SUPPORTED_LOCALES = {"en", "ar"}

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = self._create_driver()
        self.servlet = TadawulServlet()

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

    def set_locale(self, locale: str):
        """
        Set the Tadawul website language.

        Supported locales:
            en - English
            ar - Arabic
        """
        locale = locale.lower()

        if locale not in self.SUPPORTED_LOCALES:
            raise ValueError(
                f"Unsupported locale '{locale}'. "
                f"Supported locales: {sorted(self.SUPPORTED_LOCALES)}"
            )

        self.driver.get(self.BASE_URL)

        self.driver.add_cookie(
            {
                "name": (
                    "com.ibm.wps.state.preprocessors."
                    "locale.LanguageCookie"
                ),
                "value": locale,
                "domain": ".www.saudiexchange.sa",
                "path": "/",
            }
        )

        self.driver.refresh()

        time.sleep(3)

        html_lang = self.driver.find_element(
            "tag name",
            "html",
        ).get_attribute("lang")

        if html_lang != locale:
            raise RuntimeError(
                f"Failed to set Tadawul locale to '{locale}'. "
                f"HTML lang is '{html_lang}'."
            )

    def get_locale(self) -> str:
        """
        Return the current page HTML language.
        """
        return self.driver.find_element(
            "tag name",
            "html",
        ).get_attribute("lang")

    def get_ticker_data(self) -> str:
        """
        Extract the server-rendered tickerData JavaScript array
        from the current Tadawul page.
        """
        html = self.driver.page_source

        match = re.search(
            r"const tickerData\s*=\s*(\[.*?\])\s*;",
            html,
            re.DOTALL,
        )

        if not match:
            raise RuntimeError(
                "tickerData was not found on the current page"
            )

        return match.group(1)

    def get_company(self, symbol: str) -> dict:
        """
        Get a company record from the current page's tickerData.

        The returned data is based on the currently selected
        Tadawul locale.
        """
        ticker_data = self.get_ticker_data()

        company_pattern = (
            rf'\{{\s*'
            rf'company:\s*"{re.escape(symbol)}"'
            rf'.*?'
            rf'\}}'
        )

        company_match = re.search(
            company_pattern,
            ticker_data,
            re.DOTALL,
        )

        if not company_match:
            raise RuntimeError(
                f"Company {symbol} was not found in tickerData"
            )

        company_text = company_match.group(0)

        def get_field(field: str):
            field_match = re.search(
                rf'{field}:\s*"([^"]*)"',
                company_text,
            )

            if field_match:
                return field_match.group(1)

            return None

        return {
            "company": get_field("company"),
            "companyDisplay": get_field("companyDisplay"),
            "price": get_field("price"),
            "change": get_field("change"),
            "changePercent": get_field("changePercent"),
            "changeDomId": get_field("changeDomId"),
            "link": get_field("link"),
            "image": get_field("image"),
        }

    def get_company_link(self, symbol: str) -> str:
        company = self.get_company(symbol)

        company_link = company.get("link")

        if not company_link:
            raise RuntimeError(
                f"Link for company {symbol} was not found"
            )

        if company_link.startswith("/"):
            return self.BASE_URL + company_link

        return company_link

    def open_company(
        self,
        symbol: str,
        wait_seconds: int = 10,
    ):
        """
        Open a company profile using the profile link generated
        for the currently selected locale.
        """
        company_url = self.get_company_link(symbol)

        return self.open(
            company_url,
            wait_seconds=wait_seconds,
        )

    def close(self):
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()