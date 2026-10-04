from __future__ import annotations

import json
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from tadawul.scraper.browser import TadawulBrowser


class MutualFundScraper:
    SUPPORTED_LANGUAGES = {"en", "ar"}

    MUTUAL_FUNDS_PAGE = (
        "/wps/portal/saudiexchange/ourmarkets/"
        "funds-market-watch/mutual-funds"
    )

    LABELS = {
        "en": {
            "fund_documents": "Fund Documents",
            "fund_info": "Fund Info",
            "fund_name": "Fund Name",
            "fund_manager": "Fund Manager",
            "telephone": "Telephone",
            "website": "Website",
            "terms_and_conditions": "Terms and Conditions",
            "fact_sheet": "Fact Sheet",
            "financial_statements": "Financial Statements",
            "xbrl": "XBRL",
            "voting_policy": "Voting Policy",
            "mutual_funds": "Mutual Funds",
        },
        "ar": {
            "fund_documents": "وثائق الصندوق",
            "fund_info": "معلومات الصندوق",
            "fund_name": "اسم الصندوق",
            "fund_manager": "مدير الصندوق",
            "telephone": "الهاتف",
            "website": "الموقع الإلكتروني",
            "terms_and_conditions": "الشروط والأحكام",
            "fact_sheet": "الإفصاحات الربع سنوية",
            "financial_statements": "التقارير المالية",
            "xbrl": "لغة التقارير المرنة",
            "voting_policy": "سياسة التصويت",
            "mutual_funds": "صناديق الاستثمار",
        },
    }

    def __init__(
        self,
        language: str = "en",
        headless: bool = False,
    ):
        language = language.lower()

        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{language}'. "
                f"Supported languages: "
                f"{sorted(self.SUPPORTED_LANGUAGES)}"
            )

        self.language = language
        self.headless = headless

        self.browser = TadawulBrowser(headless=headless)
        self.browser.set_locale(language)

        self._funds_cache: dict | None = None

    @property
    def labels(self) -> dict[str, str]:
        return self.LABELS[self.language]

    def _fetch_funds_list(self) -> list[dict]:
        """Fetch list of all mutual funds from the API."""
        if self._funds_cache is not None:
            return self._funds_cache

        funds_url = urljoin(
            self.browser.BASE_URL,
            self.MUTUAL_FUNDS_PAGE,
        )

        self.browser.open(funds_url, wait_seconds=10)

        response_body = self.browser.get_response_body(
            "NJgetMutualFundsData"
        )

        if response_body is None:
            raise RuntimeError(
                "NJgetMutualFundsData response was not found"
            )

        response_json = json.loads(response_body)
        self._funds_cache = response_json.get("data", [])

        return self._funds_cache

    def get_fund(self, symbol: str) -> dict | None:
        """Get fund metadata by symbol."""
        funds = self._fetch_funds_list()

        return next(
            (
                fund
                for fund in funds
                if fund.get("symbol") == symbol
            ),
            None,
        )

    def get_all_fund_symbols(self) -> list[str]:
        """Get all mutual fund symbols."""
        funds = self._fetch_funds_list()
        return [
            fund["symbol"]
            for fund in funds
            if fund.get("symbol")
        ]

    def scrape(self, symbol: str) -> dict:
        """Scrape mutual fund profile data."""
        fund = self.get_fund(symbol)

        if fund is None:
            raise RuntimeError(
                f"Mutual fund {symbol} was not found"
            )

        profile_url = fund.get("companyUrl")

        if not profile_url:
            raise RuntimeError(
                f"Profile URL for fund {symbol} was not found"
            )

        if profile_url.startswith("/"):
            profile_url = self.browser.BASE_URL + profile_url

        self.browser.open(profile_url, wait_seconds=10)

        driver = self.browser.driver

        result = {
            "symbol": symbol,
            "fund_name": fund.get("fundName"),
            "language": self.language,
            "market": self._get_market(driver),
            "fund_info": {},
            "fund_documents": {
                "terms_and_conditions": [],
                "fact_sheet": [],
                "financial_statements": [],
                "xbrl": [],
                "voting_policy": [],
            },
        }

        # Click on Fund Info tab and extract data
        self._click_tab(driver, ".fundInfo")
        time.sleep(1)
        result["fund_info"] = self._get_fund_info(driver)

        # Click on Fund Documents tab and extract documents
        self._click_tab(driver, ".financials")
        time.sleep(1)
        result["fund_documents"] = {
            "terms_and_conditions": self._get_terms_and_conditions(driver),
            "fact_sheet": self._get_fact_sheet(driver),
            "financial_statements": self._get_financial_statements(driver),
            "xbrl": self._get_xbrl(driver),
            "voting_policy": self._get_voting_policy(driver),
        }

        return result

    def _click_tab(self, driver, tab_rel: str) -> bool:
        """Click on a tab by its rel attribute."""
        try:
            tabs = driver.find_elements(
                By.CSS_SELECTOR,
                f"li[rel='{tab_rel}']",
            )

            for tab in tabs:
                if tab.is_displayed():
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        tab,
                    )
                    time.sleep(0.3)
                    driver.execute_script(
                        "arguments[0].click();",
                        tab,
                    )
                    return True

        except Exception:
            pass

        return False

    def _get_market(self, driver) -> str | None:
        """Extract market type from the page."""
        try:
            market_element = driver.find_element(
                By.CSS_SELECTOR,
                "div.market_capital ul li",
            )

            if market_element.is_displayed():
                return market_element.text.strip()
        except Exception:
            pass

        return None

    def _get_fund_info(self, driver) -> dict:
        """Extract fund info table data."""
        result = {
            "fund_name": None,
            "fund_type": None,
            "fund_manager": None,
            "telephone": None,
            "website": None,
            "website_url": None,
        }

        try:
            containers = driver.find_elements(
                By.CSS_SELECTOR,
                "div.fundInfo",
            )

            visible_containers = [
                c for c in containers if c.is_displayed()
            ]

            if not visible_containers:
                return result

            container = visible_containers[0]

            table = container.find_element(
                By.CSS_SELECTOR,
                "table#issuerTable",
            )

            rows = table.find_elements(By.TAG_NAME, "tr")

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")

                if len(cells) < 2:
                    continue

                label = cells[0].text.strip()
                value = cells[1].text.strip()

                label_lower = label.lower()

                if "fund name" in label_lower or "اسم الصندوق" in label:
                    result["fund_name"] = value

                elif "fund info" in label_lower or "معلومات الصندوق" in label:
                    result["fund_type"] = value

                elif "fund manager" in label_lower or "مدير الصندوق" in label:
                    result["fund_manager"] = value

                elif "telephone" in label_lower or "الهاتف" in label:
                    result["telephone"] = value

                elif "website" in label_lower or "الموقع" in label:
                    result["website"] = value

                    # Extract URL from anchor tag
                    try:
                        link = cells[1].find_element(
                            By.TAG_NAME, "a"
                        )
                        result["website_url"] = link.get_attribute("href")
                    except Exception:
                        pass

        except Exception:
            pass

        return result

    def _get_terms_and_conditions(self, driver) -> list[dict]:
        """Extract Terms and Conditions documents."""
        return self._get_pdf_documents(
            driver,
            "Terms and Conditions",
            "الشروط والأحكام",
        )

    def _get_voting_policy(self, driver) -> list[dict]:
        """Extract Voting Policy documents."""
        return self._get_pdf_documents(
            driver,
            "Voting Policy",
            "سياسة التصويت",
        )

    def _get_pdf_documents(
        self,
        driver,
        en_label: str,
        ar_label: str,
    ) -> list[dict]:
        """Generic method to extract PDF documents from pdfDwlBox sections."""
        documents = []

        try:
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            pdf_boxes = soup.find_all("div", class_="pdfDwlBox")

            for box in pdf_boxes:
                header = box.find("h4")

                if not header:
                    continue

                header_text = header.get_text(strip=True)

                if en_label not in header_text and ar_label not in header_text:
                    continue

                year_box = box.find("div", class_="yearPdfDwl")

                if not year_box:
                    continue

                links = year_box.find_all("a", class_="btn-pdf")

                for link in links:
                    href = link.get("href", "")

                    if href and not href.startswith("http"):
                        href = urljoin(self.browser.BASE_URL, href)

                    date_elem = link.find_next("strong")
                    date_text = (
                        date_elem.get_text(strip=True)
                        if date_elem
                        else None
                    )

                    documents.append({
                        "url": href,
                        "date": date_text,
                    })

        except Exception:
            pass

        return documents

    def _get_fact_sheet(self, driver) -> list[dict]:
        """Extract Fact Sheet documents by year/quarter."""
        return self._get_tabular_documents(
            driver,
            "Fact Sheet",
            "الإفصاحات الربع سنوية",
            "fact_table",
        )

    def _get_financial_statements(self, driver) -> list[dict]:
        """Extract Financial Statements documents by year."""
        return self._get_tabular_documents(
            driver,
            "Financial Statements",
            "التقارير المالية",
            "financial_table",
        )

    def _get_xbrl(self, driver) -> list[dict]:
        """Extract XBRL documents by year."""
        documents = []

        try:
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            xbrl_heading = soup.find(
                "h4",
                class_="subHdng",
                string=lambda t: t and (
                    "XBRL" in t
                    or "لغة التقارير المرنة" in t
                ),
            )

            if not xbrl_heading:
                return documents

            table_div = xbrl_heading.find_next(
                "div",
                class_="financial_table",
            )

            if table_div:
                documents = self._parse_document_table(table_div)

        except Exception:
            pass

        return documents

    def _get_tabular_documents(
        self,
        driver,
        en_label: str,
        ar_label: str,
        table_class: str,
    ) -> list[dict]:
        """Extract documents from tabular format sections."""
        documents = []

        try:
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # Find the heading
            heading = soup.find(
                "h4",
                class_="subHdng",
                string=lambda t: t and (en_label in t or ar_label in t),
            )

            if not heading:
                return documents

            # Find the corresponding table container
            table_div = heading.find_next(
                "div",
                class_=table_class,
            )

            if table_div:
                documents = self._parse_document_table(table_div)

        except Exception:
            pass

        return documents

    def _parse_document_table(self, table_div) -> list[dict]:
        """Parse a document table and extract URLs with year/period info."""
        documents = []

        table = table_div.find("table")

        if not table:
            return documents

        thead = table.find("thead")
        years = []

        if thead:
            header_row = thead.find("tr")

            if header_row:
                ths = header_row.find_all("th")
                years = [
                    th.get_text(strip=True)
                    for th in ths
                    if th.get_text(strip=True)
                ]

        tbody = table.find("tbody")

        if not tbody:
            return documents

        rows = tbody.find_all("tr")

        for row in rows:
            cells = row.find_all("td")

            if not cells:
                continue

            period = cells[0].get_text(strip=True)

            for idx, cell in enumerate(cells[1:], start=0):
                link = cell.find("a", class_="btn-pdf",)

                if not link:
                     link = cell.find("a", attrs={"btn-pdf": True})
                
                if not link:
                    continue
                    
                href = link.get("href", "")

                if href and not href.startswith("http"):
                    href = urljoin(self.browser.BASE_URL, href)

                # Extract date from cell text
                cell_text = cell.get_text(strip=True)
                date_match = None

                # Try to find a date pattern (YYYY-MM-DD)
                import re
                date_pattern = re.search(
                    r"\d{4}-\d{2}-\d{2}",
                    cell_text,
                )

                if date_pattern:
                    date_match = date_pattern.group()

                year = years[idx] if idx < len(years) else None

                documents.append({
                    "url": href,
                    "year": year,
                    "period": period,
                    "date": date_match,
                })

        return documents

    def close(self):
        if self.browser:
            self.browser.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
