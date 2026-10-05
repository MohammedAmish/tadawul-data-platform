from __future__ import annotations

import re
from urllib.parse import (
    parse_qsl,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
)

from bs4 import BeautifulSoup

from tadawul.scraper.browser import TadawulBrowser


class EtfScraper:
    SUPPORTED_LANGUAGES = {"en", "ar"}

    ETF_MARKET_WATCH_PAGE = (
        "/wps/portal/saudiexchange/ourmarkets/"
        "funds-market-watch/Etfsv2/etf-market-watch"
    )

    LABELS = {
        "en": {
            "fund_profile": "Fund Profile",
            "index_info": "INDEX INFO",
            "fund_details": "Fund Details",
            "fund_chairman": "Fund Chairman",
            "fund_board_of_directors": "Fund Board of Directors",
            "senior_executives": "Senior Executives",
            "financials": "Financials",
            "terms_and_conditions": "Terms and Conditions",
            "basket_components": "Basket Components",
            "investor_relations": "Investor Relations",
            "date_established": "Date Established",
            "financial_year_end": "Financial Year End",
            "listing_date": "Listing Date",
            "external_auditors": "External Auditors",
            "isin_code": "ISIN CODE",
            "number_of_employees": "Number of Employees",
            "contact_name": "Contact Name:",
            "address": "Address",
            "contact_information": "Contact Information",
            "website": "Website:",
        },
        "ar": {
            "fund_profile": "ملف الصندوق",
            "index_info": "معلومات المؤشر",
            "fund_details": "تفاصيل الصندوق",
            "fund_chairman": "رئيس مجلس إدارة الصندوق",
            "fund_board_of_directors": "مجلس إدارة الصندوق",
            "senior_executives": "كبار التنفيذيين",
            "financials": "البيانات المالية",
            "terms_and_conditions": "الشروط والاحكام",
            "basket_components": "مكونات الصندوق",
            "investor_relations": "علاقات المستثمرين",
            "date_established": "تاريخ التأسيس",
            "financial_year_end": "نهاية السنة المالية",
            "listing_date": "تاريخ الادراج",
            "external_auditors": "مراجعي الحسابات",
            "isin_code": "الرمز الدولي",
            "number_of_employees": "عدد الموظفين",
            "contact_name": "اسم ضابط الاتصال",
            "address": "العنوان",
            "contact_information": "بيانات الإتصال",
            "website": "اسم موقع الانترنت:",
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

        self.browser = TadawulBrowser(
            headless=headless
        )

        self.browser.set_locale(language)

    @property
    def labels(self) -> dict[str, str]:
        return self.LABELS[self.language]

    def _set_url_locale(
        self,
        url: str,
    ) -> str:
        """Force the ETF profile URL to use the scraper language."""
        parsed = urlparse(url)

        query = dict(
            parse_qsl(
                parsed.query
            )
        )

        query["locale"] = self.language

        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                urlencode(query),
                parsed.fragment,
            )
        )

    def get_all_etfs(self) -> list[dict]:
        """Get all ETFs from the ETF market-watch page."""
        market_watch_url = urljoin(
            self.browser.BASE_URL,
            self.ETF_MARKET_WATCH_PAGE,
        )

        self.browser.open(
            market_watch_url,
            wait_seconds=5,
        )

        soup = BeautifulSoup(
            self.browser.driver.page_source,
            "html.parser",
        )

        table = soup.select_one(
            "#table12"
        )

        if table is None:
            raise RuntimeError(
                "ETF market-watch table was not found"
            )

        etfs = []

        for link in table.select(
            'a[href*="company-profile-etf"]'
        ):
            name = link.get_text(
                " ",
                strip=True,
            )

            href = link.get(
                "href"
            )

            if not href:
                continue

            etfs.append(
                {
                    "name": name,
                    "url": urljoin(
                        self.browser.BASE_URL,
                        href,
                    ),
                }
            )

        return etfs

    def scrape(
        self,
        url: str,
    ) -> dict:
        """Scrape ETF profile data."""

        url = self._set_url_locale(
            url
        )

        self.browser.open(
            url,
            wait_seconds=5,
        )

        soup = BeautifulSoup(
            self.browser.driver.page_source,
            "html.parser",
        )

        return {
            "symbol": self._parse_symbol(
                soup
            ),
            "etf_name": self._parse_etf_name(
                soup
            ),
            "language": self.language,
            "fund_profile": self._parse_fund_profile(
                soup
            ),
            "fund_details": self._parse_fund_details(
                soup
            ),
            "management": self._parse_management(
                soup
            ),
            "financials": self._parse_financials(
                soup
            ),
            "terms_and_conditions": self._parse_terms(
                soup
            ),
            "basket_components": self._parse_basket(
                soup
            ),
            "investor_relations": (
                self._parse_investor_relations(
                    soup
                )
            ),
        }

    def _parse_symbol(
        self,
        soup: BeautifulSoup,
    ) -> str | None:
        """Extract ETF symbol from the stats overview."""
        section = soup.select_one(
            "div.saudiCable.stats_overview"
        )

        if section is None:
            return None

        price_name = section.select_one(
            "div.price_name"
        )

        if price_name is None:
            return None

        price = price_name.select_one(
            "div.price"
        )

        if price is None:
            return None

        return price.get_text(
            " ",
            strip=True,
        )

    def _parse_etf_name(
        self,
        soup: BeautifulSoup,
    ) -> str | None:
        """Extract ETF name from the stats overview."""
        section = soup.select_one(
            "div.saudiCable.stats_overview"
        )

        if section is None:
            return None

        price_name = section.select_one(
            "div.price_name"
        )

        if price_name is None:
            return None

        name = price_name.select_one(
            "div.name"
        )

        if name is None:
            return None

        return name.get_text(
            " ",
            strip=True,
        )

    def _parse_fund_profile(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        """Extract ETF fund profile information."""
        section = soup.select_one(
            "div.fundInfo"
        )

        if section is None:
            return {}

        result = {}

        paragraphs = section.find_all(
            "p",
            recursive=False,
        )

        if paragraphs:
            result["description"] = paragraphs[
                0
            ].get_text(
                " ",
                strip=True,
            )

        index_labels = {
            self.LABELS["en"]["index_info"],
            self.LABELS["ar"]["index_info"],
        }

        for index, paragraph in enumerate(
            paragraphs
        ):
            strong = paragraph.find(
                "strong"
            )

            if not strong:
                continue

            label = strong.get_text(
                " ",
                strip=True,
            )

            if any(
                label.upper()
                == index_label.upper()
                for index_label in index_labels
            ):
                if index + 1 < len(
                    paragraphs
                ):
                    result["index_info"] = (
                        paragraphs[index + 1]
                        .get_text(
                            " ",
                            strip=True,
                        )
                    )

                break

        inspection_box = section.select_one(
            "div.inspectionBox"
        )

        if inspection_box:
            for item in inspection_box.select(
                "li"
            ):
                label = item.find(
                    "span"
                )

                value = item.find(
                    "strong"
                )

                if not label or not value:
                    continue

                key = self._normalise_key(
                    label.get_text(
                        " ",
                        strip=True,
                    )
                )

                result[key] = value.get_text(
                    " ",
                    strip=True,
                )

        return result

    def _parse_fund_details(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        """Extract ETF fund details."""
        sections = soup.select(
            "div.company_management_tab_dtl"
        )

        if not sections:
            return {}

        detail_labels = {
            self.LABELS["en"]["date_established"],
            self.LABELS["en"]["isin_code"],
            self.LABELS["ar"]["date_established"],
            self.LABELS["ar"]["isin_code"],
        }

        for section in sections:
            headings = section.find_all(
                "h4"
            )

            labels = {
                heading.get_text(
                    " ",
                    strip=True,
                )
                for heading in headings
            }

            if labels & detail_labels:
                return self._parse_label_value_section(
                    section
                )

        return {}

    def _parse_management(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        """Extract fund chairman, board and senior executives."""

        result = {
            "fund_chairman": [],
            "fund_board_of_directors": [],
        }

        designation_map = {
            "Fund Chairman": "fund_chairman",
            "رئيس مجلس إدارة الصندوق": "fund_chairman",

            "Fund Board of Directors": (
                "fund_board_of_directors"
            ),
            "مجلس إدارة الصندوق": (
                "fund_board_of_directors"
            ),
            "أعضاء مجلس إدارة الصندوق": (
                            "fund_board_of_directors"
            ),
        }

        for section in soup.select(
            "div.company_management_tab_dtl"
        ):
            if not section.select_one(
                "div.namePopupBox"
            ):
                continue

            for popup in section.select(
                "div.namePopupBox"
            ):
                person = (
                    self._parse_management_person(
                        popup
                    )
                )

                if not person:
                    continue

                designation = person.get(
                    "designation",
                    "",
                ).strip()

                target = designation_map.get(
                    designation
                )

                if target:
                    result[target].append(
                        person
                    )

        return result

    def _parse_management_person(
        self,
        popup,
    ) -> dict:
        """Extract one management person's details."""

        heading = popup.select_one(
            ".hdng"
        )

        if not heading:
            return {}

        person = {
            "name": heading.get_text(
                " ",
                strip=True,
            )
        }

        fields = popup.select(
            ".topTxt"
        )

        values = popup.select(
            ".btmTxt"
        )

        for label, value in zip(
            fields,
            values,
        ):
            key = self._normalise_key(
                label.get_text(
                    " ",
                    strip=True,
                )
            )

            person[key] = value.get_text(
                " ",
                strip=True,
            )

        return person

    def _parse_financials(
        self,
        soup: BeautifulSoup,
    ) -> list[dict]:
        """Extract financial statement documents."""
        section = soup.select_one(
            "div.financials"
        )

        if section is None:
            return []

        table = section.find(
            "table"
        )

        if table is None:
            return []

        header_row = table.select_one(
            "thead tr"
        )

        if header_row is None:
            return []

        header_cells = header_row.find_all(
            "th"
        )

        year_columns = []

        for column_index, cell in enumerate(
            header_cells
        ):
            text = cell.get_text(
                " ",
                strip=True,
            )

            if re.fullmatch(
                r"\d{4}",
                text,
            ):
                year_columns.append(
                    (
                        column_index,
                        text,
                    )
                )

        if not year_columns:
            return []

        tbody = table.find(
            "tbody"
        )

        if tbody is None:
            return []

        documents = []

        for row in tbody.find_all(
            "tr"
        ):
            cells = row.find_all(
                "td"
            )

            if not cells:
                continue

            period = cells[0].get_text(
                " ",
                strip=True,
            )

            for cell_index, year in year_columns:
                if cell_index >= len(
                    cells
                ):
                    continue

                cell = cells[
                    cell_index
                ]

                link = cell.find(
                    "a",
                    class_="btn-pdf",
                )

                if not link:
                    continue

                href = link.get(
                    "href",
                    "",
                )

                if href and not href.startswith(
                    "http"
                ):
                    href = urljoin(
                        self.browser.BASE_URL,
                        href,
                    )

                cell_text = cell.get_text(
                    " ",
                    strip=True,
                )

                date_match = re.search(
                    r"\d{4}-\d{2}-\d{2}",
                    cell_text,
                )

                date = (
                    date_match.group()
                    if date_match
                    else None
                )

                documents.append(
                    {
                        "url": href,
                        "year": year,
                        "period": period,
                        "date": date,
                    }
                )

        return documents

    def _parse_terms(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        """Extract Terms and Conditions URL."""
        link = soup.select_one(
            "div.etfTermBtn a"
        )

        if not link:
            return {}

        return {
            "name": link.get_text(
                " ",
                strip=True,
            ),
            "url": urljoin(
                self.browser.BASE_URL,
                link.get(
                    "href",
                    "",
                ),
            ),
        }

    def _parse_basket(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        """Extract Basket Components URL."""
        link = soup.select_one(
            "div.etfBasketBtn a"
        )

        if not link:
            return {}

        return {
            "name": link.get_text(
                " ",
                strip=True,
            ),
            "url": link.get(
                "href"
            ),
        }

    def _parse_investor_relations(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        """Extract Investor Relations information."""
        section = soup.select_one(
            "div.investor_relations"
        )

        if section is None:
            return {}

        result = {}

        label_map = {
            self.LABELS["en"]["contact_name"]:
                "contact_name",
            self.LABELS["ar"]["contact_name"]:
                "contact_name",

            self.LABELS["en"]["address"]:
                "address",
            self.LABELS["ar"]["address"]:
                "address",

            self.LABELS["en"]["contact_information"]:
                "contact_information",
            self.LABELS["ar"]["contact_information"]:
                "contact_information",

            self.LABELS["en"]["website"]:
                "website",
            self.LABELS["ar"]["website"]:
                "website",
        }

        for heading in section.find_all(
            "h4"
        ):
            label = heading.get_text(
                " ",
                strip=True,
            )

            key = label_map.get(
                label
            )

            if key is None:
                continue

            value = heading.find_next_sibling()

            if value is None:
                continue

            if key == "contact_information":
                result[key] = value.get_text(
                    " ",
                    strip=True,
                )

                email = value.select_one(
                    'a[href^="mailto:"]'
                )

                if email:
                    result["email"] = (
                        email.get_text(
                            " ",
                            strip=True,
                        )
                    )

                continue

            if key == "website":
                link = value.find(
                    "a"
                )

                if link:
                    result["website"] = (
                        link.get_text(
                            " ",
                            strip=True,
                        )
                    )

                    result["website_url"] = (
                        link.get("href")
                    )
                else:
                    result["website"] = (
                        value.get_text(
                            " ",
                            strip=True,
                        )
                    )

                continue

            result[key] = value.get_text(
                " ",
                strip=True,
            )

        return result

    @staticmethod
    def _parse_label_value_section(
        section,
    ) -> dict:
        """Extract values from h4/p label-value pairs."""
        result = {}

        for item in section.select(
            "li"
        ):
            heading = item.find(
                "h4"
            )

            value = item.find(
                "p"
            )

            if not heading or not value:
                continue

            key = EtfScraper._normalise_key(
                heading.get_text(
                    " ",
                    strip=True,
                )
            )

            result[key] = value.get_text(
                " ",
                strip=True,
            )

        return result

    @staticmethod
    def _normalise_key(
        value: str,
    ) -> str:
        """Convert a label into a language-independent key."""

        value = value.replace(
            "\xa0",
            " ",
        )

        value = re.sub(
            r"\s*\^+\s*",
            " ",
            value,
        )

        value = re.sub(
            r"[()]+",
            "",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

        key_map = {
            # English - Fund Details
            "Date Established": "date_established",
            "Financial Year End": "financial_year_end",
            "Listing Date": "listing_date",
            "External Auditors": "external_auditors",
            "ISIN CODE": "isin_code",
            "Number of Employees": "number_of_employees",

            # Arabic - Fund Details
            "تاريخ التأسيس": "date_established",
            "نهاية السنة المالية": "financial_year_end",
            "تاريخ الادراج": "listing_date",
            "مراجعي الحسابات": "external_auditors",
            "الرمز الدولي": "isin_code",
            "عدد الموظفين": "number_of_employees",

            # English - Fund Profile
            "Net Assets at Inception":
                "initial_net_assets",
            "Total Units at Inception":
                "initial_total_units",
            "Initial Unit Value":
                "initial_unit_value",

            # Arabic - Fund Profile
            "صافي الأصول عند التأسيس":
                "initial_net_assets",
            "إجمالي الوحدات عند التأسيس":
                "initial_total_units",
            "القيمة المبدئية للوحدات":
                "initial_unit_value",

            # English - Management
            "BD Session Start":
                "bd_session_start",
            "BD Session End":
                "bd_session_end",
            "Designation":
                "designation",
            "Classification":
                "classification",
            "Classsification":
                "classification",

            # Arabic - Management
            "تاريخ بدء الجلسة":
                "bd_session_start",
            "تاريخ نهاية الجلسة":
                "bd_session_end",
            "صفة العضوية":
                "designation",
            "التصنيف":
                "classification",
        }

        if value in key_map:
            return key_map[value]

        # Fallback for unmapped English labels.
        value = re.sub(
            r"[^a-zA-Z0-9]+",
            "_",
            value,
        )

        return value.strip(
            "_"
        ).lower()

    def close(self):
        if self.browser:
            self.browser.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        self.close()