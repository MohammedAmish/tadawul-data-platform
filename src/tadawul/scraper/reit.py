from __future__ import annotations

import re
import time

from urllib.parse import (
    parse_qsl,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
)

from bs4 import BeautifulSoup

from tadawul.scraper.browser import TadawulBrowser


class ReitScraper:
    SUPPORTED_LANGUAGES = {"en", "ar"}

    REIT_MARKET_WATCH_PAGE = (
        "/wps/portal/saudiexchange/ourmarkets/"
        "funds-market-watch/reits"
    )

    LABELS = {
        "en": {
            "fund_overview": "Fund Overview",
            "managed_assets": "Managed Assets",
            "terms_and_conditions": "Terms and Conditions",
            "units_profile": "Units Profile",
            "investment_limits": "Investment limits",

            "date_established": "Date Established",
            "financial_year_end": "Financial Year End",
            "listing_date": "Listing Date",
            "external_auditors": "External Auditors",
            "isin_code": "ISIN CODE",
            "number_of_employees": "Number of Employees",

            "fund_chairman": "Fund Chairman",
            "fund_board_of_directors": (
                "Fund Board of Directors"
            ),

            "contact_name": "Contact Name",
            "company_address": "Company Address",
            "contact_details": "Contact Details",
            "company_website": "Company Website",

            "financials_tab": "Quarterly Report",
            "substantial_shareholders_tab": (
                "Substantial Shareholders"
            ),

            "last_update": "Last Update",

            "total_foreign_ownership": (
                "Total Foreign ownership"
            ),
            "foreign_strategic_investors": (
                "Foreign strategic investors"
            ),

            "popup_bd_session_start": (
                "BD Session Start"
            ),
            "popup_designation": "Designation",
            "popup_bd_session_end": (
                "BD Session End"
            ),
            "popup_classification": "Classification",

            "terms_link": "Click here",
        },

        "ar": {
            "fund_overview": "نظرة عامة على الصندوق",
            "managed_assets": "الأصول",
            "terms_and_conditions": "الشروط والاحكام",
            "units_profile": "وحدات الصندوق",
            "investment_limits": "قيود الاستثمار",

            "date_established": "تاريخ التأسيس",
            "financial_year_end": "نهاية السنة المالية",
            "listing_date": "تاريخ الادراج",
            "external_auditors": "مراجعي الحسابات",
            "isin_code": "الرمز الدولي",
            "number_of_employees": "عدد الموظفين",

            "fund_chairman": (
                "رئيس مجلس إدارة الصندوق"
            ),
            "fund_board_of_directors": (
                "أعضاء مجلس إدارة الصندوق"
            ),

            "contact_name": "اسم ضابط الاتصال",
            "company_address": "عنوان الشركة",
            "contact_details": "بيانات الإتصال",
            "company_website": "موقع الشركة",

            "financials_tab": (
                "الإفصاحات الربع سنوية"
            ),
            "substantial_shareholders_tab": (
                "المساهمون الكبار"
            ),

            "last_update": "آخر تحديث",

            "total_foreign_ownership": (
                "ملكيه جميع المستثمرين الاجانب"
            ),
            "foreign_strategic_investors": (
                "ملكية المستثمر الاستراتيجي الأجنبي"
            ),

            "popup_bd_session_start": (
                "تاريخ بداية دورة المجلس"
            ),
            "popup_designation": "منصب",
            "popup_bd_session_end": (
                "تاريخ نهاية دورة المجلس"
            ),
            "popup_classification": "صفة العضوية",

            "terms_link": "انقر هنا",
        },
    }

    UNIT_KEYS = {
        "en": {
            "Authorized Capital": "authorized_capital",
            "No.Of Units": "number_of_units",
            "Paid Capital": "paid_capital",
            "Par Value/Unit": "par_value_per_unit",
            "Paid Up Value/Unit": "paid_up_value_per_unit",
        },

        "ar": {
            "رأس المال المصرّح": "authorized_capital",
            "رأس المال المصرح": "authorized_capital",
            "عدد الوحدات": "number_of_units",
            "رأس المال المدفوع": "paid_capital",
            "القيمة الاسمية/الوحدة": (
                "par_value_per_unit"
            ),
            "القيمة المدفوعة/الوحدة": (
                "paid_up_value_per_unit"
            ),
        },
    }

    def __init__(
        self,
        language: str = "en",
        headless: bool = True,
    ):
        language = language.lower()

        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{language}'. "
                f"Supported languages: "
                f"{sorted(self.SUPPORTED_LANGUAGES)}"
            )

        self.language = language

        self.browser = TadawulBrowser(
            headless=headless
        )

        self.browser.set_locale(
            self.language
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _clean_value(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = " ".join(
            value.split()
        )

        return value if value else None

    @staticmethod
    def _normalise_label(
        value: str | None,
    ) -> str:
        if not value:
            return ""

        return (
            " ".join(value.split())
            .strip()
            .lower()
            .rstrip(":")
            .strip()
        )

    @staticmethod
    def _normalise_key(
        value: str,
    ) -> str:
        return (
            value.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    def _get_label_value(
        self,
        container,
        label: str,
    ) -> str | None:
        """
        Find the value associated with a label.

        Handles Tadawul layouts where the label and
        value are stored in adjacent elements.
        """
        if container is None:
            return None

        target = self._normalise_label(
            label
        )

        for element in container.find_all(
            recursive=True
        ):
            text = self._normalise_label(
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if text != target:
                continue

            sibling = (
                element.find_next_sibling()
            )

            if sibling:
                value = self._clean_value(
                    sibling.get_text(
                        " ",
                        strip=True,
                    )
                )

                if (
                    value
                    and self._normalise_label(
                        value
                    ) != target
                ):
                    return value

            next_element = element.find_next()

            if (
                next_element
                and next_element is not element
            ):
                value = self._clean_value(
                    next_element.get_text(
                        " ",
                        strip=True,
                    )
                )

                if (
                    value
                    and self._normalise_label(
                        value
                    ) != target
                ):
                    return value

        return None

    # ---------------------------------------------------------
    # URL locale
    # ---------------------------------------------------------

    def _set_url_locale(
        self,
        url: str,
    ) -> str:
        parsed = urlparse(url)

        query = dict(
            parse_qsl(
                parsed.query,
                keep_blank_values=True,
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

    # ---------------------------------------------------------
    # REIT discovery
    # ---------------------------------------------------------

    def get_all_reits(
        self,
    ) -> list[dict]:
        market_watch_url = (
            self.browser.BASE_URL
            + self.REIT_MARKET_WATCH_PAGE
        )

        market_watch_url = (
            self._set_url_locale(
                market_watch_url
            )
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
            "#reitsTable"
        )

        if table is None:
            print("REIT table not found")
            return []

        reits = []

        for link in table.select(
            "a[href]"
        ):
            reit_name = link.get_text(
                " ",
                strip=True,
            )

            href = link.get(
                "href"
            )

            if not reit_name or not href:
                continue

            reit_url = urljoin(
                self.browser.BASE_URL,
                href,
            )

            reit_url = self._set_url_locale(
                reit_url
            )

            reits.append(
                {
                    "reit_name": reit_name,
                    "url": reit_url,
                }
            )

        return reits

    # ---------------------------------------------------------
    # Scrape one REIT
    # ---------------------------------------------------------

    def scrape(
        self,
        url: str,
    ) -> dict:
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

        reit_name = self._parse_reit_name(
            soup
        )

        symbol = self._parse_symbol(
            soup
        )

        result = {
            "reit_name": reit_name,
            "symbol": symbol,
            "language": self.language,
            "market": self._parse_market(
                soup
            ),
            "category": self._parse_category(
                soup
            ),
            "fund_profile": (
                self._parse_fund_profile(
                    soup
                )
            ),
            "fund_details": (
                self._parse_fund_details(
                    soup
                )
            ),
            "management": (
                self._parse_management(
                    soup
                )
            ),
            "investor_relations": (
                self._parse_investor_relations(
                    soup
                )
            ),
            "financials": (
                self._parse_financials(
                    soup
                )
            ),
            "foreign_ownership": {},
            "substantial_shareholders": {
                "substantial_shareholders": [],
                "shareholders_subject_to_lock_up": [],
            },
        }

        self._scrape_shareholding(
            result
        )

        return result

    # ---------------------------------------------------------
    # Basic profile
    # ---------------------------------------------------------

    @staticmethod
    def _parse_reit_name(
        soup: BeautifulSoup,
    ) -> str | None:
        element = soup.select_one(
            ".price_name .name"
        )

        if element:
            return element.get_text(
                " ",
                strip=True,
            )

        return None

    @staticmethod
    def _parse_symbol(
        soup: BeautifulSoup,
    ) -> str | None:
        element = soup.select_one(
            ".price_name .price"
        )

        if element:
            return element.get_text(
                " ",
                strip=True,
            )

        return None

    @staticmethod
    def _parse_market(
        soup: BeautifulSoup,
    ) -> str | None:
        section = soup.select_one(
            "div.market_capital"
        )

        if section is None:
            return None

        items = section.select(
            "ul > li"
        )

        if len(items) >= 1:
            return items[0].get_text(
                " ",
                strip=True,
            )

        return None

    @staticmethod
    def _parse_category(
        soup: BeautifulSoup,
    ) -> str | None:
        section = soup.select_one(
            "div.market_capital"
        )

        if section is None:
            return None

        items = section.select(
            "ul > li"
        )

        if len(items) >= 2:
            return items[1].get_text(
                " ",
                strip=True,
            )

        return None

    # ---------------------------------------------------------
    # Fund Profile
    # ---------------------------------------------------------

    def _parse_fund_profile(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        labels = self.LABELS[
            self.language
        ]

        section = soup.select_one(
            "div.fundInfo"
        )

        if section is None:
            return {}

        result = {
            "fund_overview": None,
            "managed_assets": None,
            "terms_and_conditions": {
                "text": None,
                "href": None,
            },
            "units_profile": {
                "authorized_capital": None,
                "number_of_units": None,
                "paid_capital": None,
                "par_value_per_unit": None,
                "paid_up_value_per_unit": None,
                "last_update": None,
            },
            "investment_limits": None,
        }

        paragraphs = section.select("p")

        for index, paragraph in enumerate(
            paragraphs
        ):
            strong = paragraph.find("strong")

            if strong is None:
                continue

            heading = self._clean_value(
                strong.get_text(
                    " ",
                    strip=True,
                )
            )

            normalized_heading = (
                self._normalise_label(
                    heading
                )
            )

            if normalized_heading == self._normalise_label(
                labels["fund_overview"]
            ):
                if index + 1 < len(paragraphs):
                    result["fund_overview"] = (
                        self._clean_value(
                            paragraphs[index + 1].get_text(
                                " ",
                                strip=True,
                            )
                        )
                    )

            elif normalized_heading == self._normalise_label(
                labels["managed_assets"]
            ):
                if index + 1 < len(paragraphs):
                    result["managed_assets"] = (
                        self._clean_value(
                            paragraphs[index + 1].get_text(
                                " ",
                                strip=True,
                            )
                        )
                    )

            elif normalized_heading == self._normalise_label(
                labels["terms_and_conditions"]
            ):
                if index + 1 < len(paragraphs):
                    content = paragraphs[index + 1]

                    link = content.find(
                        "a",
                        href=True,
                    )

                    if link:
                        result[
                            "terms_and_conditions"
                        ] = {
                            "text": self._clean_value(
                                link.get_text(
                                    " ",
                                    strip=True,
                                )
                            ),
                            "href": urljoin(
                                self.browser.BASE_URL,
                                link["href"],
                            ),
                        }

            elif normalized_heading == self._normalise_label(
                labels["units_profile"]
            ):
                units_box = paragraph.find_next(
                    "div",
                    class_="inspectionBox",
                )

                if units_box:
                    unit_keys = self.UNIT_KEYS[
                        self.language
                    ]

                    for item in units_box.select(
                        "ul > li"
                    ):
                        label = item.find("span")
                        value = item.find("strong")

                        if not label or not value:
                            continue

                        label_text = label.get_text(
                            " ",
                             strip=True,
                        )
                        
                        label_text = label_text.replace(
                            "^",
                            "",
                        )
                        
                        label_text = label_text.replace(
                            "(",
                            "",
                        )
                        
                        label_text = label_text.replace(
                            ")",
                            "",
                        )
                        
                        label_text = self._clean_value(
                            label_text
                        )
                        
                        value_text = self._clean_value(
                            value.get_text(
                                " ",
                                strip=True,
                            )
                        )

                        normalized_label = (
                            self._normalise_label(
                                label_text
                            )
                        )

                        for (
                            source_label,
                            output_key,
                        ) in unit_keys.items():

                            if normalized_label == self._normalise_label(
                                source_label
                            ):
                                result[
                                    "units_profile"
                                ][
                                    output_key
                                ] = value_text

                                break

                    last_update = units_box.find("p")

                    if last_update:
                        last_update_text = (
                            self._clean_value(
                                last_update.get_text(
                                    " ",
                                    strip=True,
                                )
                            )
                        )

                        if last_update_text:
                            if self.language == "ar":
                                last_update_text = re.sub(
                                    r"^آخر تحديث\s*:?\s*",
                                    "",
                                    last_update_text,
                                )

                                last_update_text = re.sub(
                                    r"^تاريخ آخر تحديث\s*:?\s*",
                                    "",
                                    last_update_text,
                                )
                            else:
                                last_update_text = re.sub(
                                    r"^Last Update\s*:?\s*",
                                    "",
                                    last_update_text,
                                    flags=re.IGNORECASE,
                                )

                            result[
                                "units_profile"
                            ][
                                "last_update"
                            ] = last_update_text.strip()

        for heading in section.find_all("h2"):
            heading_text = self._clean_value(
                heading.get_text(
                    " ",
                    strip=True,
                )
            )

            if self._normalise_label(
                heading_text
            ) == self._normalise_label(
                labels["investment_limits"]
            ):
                for paragraph in heading.find_all_next("p"):
                    value = self._clean_value(
                        paragraph.get_text(
                            " ",
                            strip=True,
                        )
                    )

                    if value:
                        result[
                            "investment_limits"
                        ] = value
                        break

                break

        return result

    # ---------------------------------------------------------
    # Fund Details
    # ---------------------------------------------------------

    def _parse_fund_details(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        labels = self.LABELS[
            self.language
        ]

        section = soup.select_one(
            "div.company_management_tab_dtl"
        )

        if section is None:
            return {}

        result = {
            "date_established": None,
            "financial_year_end": None,
            "listing_date": None,
            "external_auditors": None,
            "isin_code": None,
            "number_of_employees": None,
        }

        field_mapping = {
            "date_established": labels[
                "date_established"
            ],
            "financial_year_end": labels[
                "financial_year_end"
            ],
            "listing_date": labels[
                "listing_date"
            ],
            "external_auditors": labels[
                "external_auditors"
            ],
            "isin_code": labels[
                "isin_code"
            ],
            "number_of_employees": labels[
                "number_of_employees"
            ],
        }

        for output_key, label in (
            field_mapping.items()
        ):
            result[
                output_key
            ] = self._get_label_value(
                section,
                label,
            )

        return result

    # ---------------------------------------------------------
    # Management
    # ---------------------------------------------------------

    def _parse_management(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        labels = self.LABELS[
            self.language
        ]

        result = {
            "fund_chairman": [],
            "fund_board_of_directors": [],
        }

        designation_map = {
            self._normalise_label(
                labels["fund_chairman"]
            ): "fund_chairman",

            self._normalise_label(
                labels[
                    "fund_board_of_directors"
                ]
            ): "fund_board_of_directors",
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

                designation = self._clean_value(
                    person.get(
                        "designation"
                    )
                )

                if not designation:
                    continue

                target = designation_map.get(
                    self._normalise_label(
                        designation
                    )
                )

                if target:
                    result[
                        target
                    ].append(person)

        return result

    def _parse_management_person(
        self,
        popup,
    ) -> dict:
        labels = self.LABELS[
            self.language
        ]

        heading = popup.select_one(
            ".hdng"
        )

        if not heading:
            return {}

        person = {
            "name": self._clean_value(
                heading.get_text(
                    " ",
                    strip=True,
                )
            ),
            "bd_session_start": None,
            "designation": None,
            "bd_session_end": None,
            "classification": None,
        }

        label_mapping = {
            self._normalise_label(
                labels[
                    "popup_bd_session_start"
                ]
            ): "bd_session_start",

            self._normalise_label(
                labels[
                    "popup_designation"
                ]
            ): "designation",

            self._normalise_label(
                labels[
                    "popup_bd_session_end"
                ]
            ): "bd_session_end",

            self._normalise_label(
                labels[
                    "popup_classification"
                ]
            ): "classification",
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
            source_label = self._clean_value(
                label.get_text(
                    " ",
                    strip=True,
                )
            )

            value_text = self._clean_value(
                value.get_text(
                    " ",
                    strip=True,
                )
            )

            output_key = label_mapping.get(
                self._normalise_label(
                    source_label
                )
            )

            if output_key:
                person[
                    output_key
                ] = value_text

        return person

    # ---------------------------------------------------------
    # Investor Relations
    # ---------------------------------------------------------

    def _parse_investor_relations(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        labels = self.LABELS[
            self.language
        ]

        section = soup.select_one(
            "div.investor_relations"
        )

        if section is None:
            return {}

        result = {
            "contact_name": None,
            "company_address": None,
            "telephone": None,
            "fax": None,
            "email": None,
            "website": None,
        }

        field_mapping = {
            "contact_name": labels[
                "contact_name"
            ],
            "company_address": labels[
                "company_address"
            ],
        }

        for output_key, label in (
            field_mapping.items()
        ):
            result[
                output_key
            ] = self._get_label_value(
                section,
                label,
            )

        contact_details = (
            self._get_label_value(
                section,
                labels["contact_details"],
            )
        )

        if contact_details:
            if self.language == "ar":
                telephone_match = re.search(
                    r"(?:الهاتف|هاتف)\s*[:：]?\s*([^\s،,]+)",
                    contact_details,
                )

                fax_match = re.search(
                    r"(?:فاكس)\s*[:：]?\s*([^\s،,]+)",
                    contact_details,
                )

            else:
                telephone_match = re.search(
                    r"Telephone\s*:\s*([^\s,]+)",
                    contact_details,
                    re.IGNORECASE,
                )

                fax_match = re.search(
                    r"Fax\s*:\s*([^\s,]+)",
                    contact_details,
                    re.IGNORECASE,
                )

            if telephone_match:
                result[
                    "telephone"
                ] = telephone_match.group(
                    1
                )

            if fax_match:
                result[
                    "fax"
                ] = fax_match.group(
                    1
                )

        email = section.select_one(
            'a[href^="mailto:"]'
        )

        if email:
            result[
                "email"
            ] = (
                email.get(
                    "href",
                    "",
                )
                .replace(
                    "mailto:",
                    "",
                )
                .strip()
            )

            if not result["email"]:
                result[
                    "email"
                ] = self._clean_value(
                    email.get_text(
                        " ",
                        strip=True,
                    )
                )

        website = section.select_one(
            'a[href^="http"]'
        )

        if website:
            result[
                "website"
            ] = website.get(
                "href"
            )

        return result

    # ---------------------------------------------------------
    # Financials
    # ---------------------------------------------------------

    def _parse_financials(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        section = soup.select_one(
            "div.financials, "
            "div.financials_Reits"
        )

        if section is None:
            return {}

        result = {
            "reports": [],
        }

        tabs = [
            tab.get_text(
                " ",
                strip=True,
            )
            for tab in section.select(
                ".financials_Tab li, "
                ".financials_Tab_Reits li"
            )
        ]

        financial_sections = section.select(
            ".financials_Tab_Dtl_box > "
            ".inner_tab_DtlBox, "
            ".financials_Tab_Dtl_box_Reits > "
            ".inner_tab_DtlBox_Reits"
        )

        for index, financial_section in enumerate(
            financial_sections
        ):
            if index >= len(tabs):
                continue

            report_type = tabs[
                index
            ]

            for table in financial_section.select(
                "table"
            ):
                headers = [
                    th.get_text(
                        " ",
                        strip=True,
                    )
                    for th in table.select(
                        "thead th"
                    )
                ]

                if not headers:
                    continue

                for row in table.select(
                    "tbody tr"
                ):
                    cells = row.find_all(
                        "td"
                    )

                    if not cells:
                        continue

                    period = cells[
                        0
                    ].get_text(
                        " ",
                        strip=True,
                    )

                    for (
                        cell_index,
                        cell,
                    ) in enumerate(
                        cells[1:],
                        start=1,
                    ):
                        year = (
                            headers[
                                cell_index
                            ]
                            if cell_index
                            < len(headers)
                            else None
                        )

                        link = cell.select_one(
                            "a[href]"
                        )

                        report = {
                            "report_type": (
                                report_type
                            ),
                            "period": period,
                            "year": year,
                            "date": (
                                cell.get_text(
                                    " ",
                                    strip=True,
                                )
                            ),
                            "href": None,
                        }

                        if link:
                            report[
                                "href"
                            ] = urljoin(
                                self.browser.BASE_URL,
                                link["href"],
                            )

                        result[
                            "reports"
                        ].append(
                            report
                        )

        return result

    # ---------------------------------------------------------
    # Shareholding
    # ---------------------------------------------------------

    def _scrape_shareholding(
        self,
        result: dict,
    ):
        self.browser.driver.get_log(
            "performance"
        )

        tabs = (
            self.browser.driver.find_elements(
                "css selector",
                ".shareholding_tab li",
            )
        )

        if len(tabs) < 3:
            return

        # -----------------------------------------------------
        # Foreign Ownership
        # -----------------------------------------------------

        self.browser.driver.execute_script(
            "arguments[0].click();",
            tabs[1],
        )

        time.sleep(3)

        foreign_html = (
            self.browser.get_response_body(
                "NJforeginOwnerShip"
            )
        )

        if foreign_html:
            soup = BeautifulSoup(
                foreign_html,
                "html.parser",
            )

            result[
                "foreign_ownership"
            ] = (
                self._parse_foreign_ownership(
                    soup
                )
            )

        # -----------------------------------------------------
        # Clear logs before second request
        # -----------------------------------------------------

        self.browser.driver.get_log(
            "performance"
        )

        tabs = (
            self.browser.driver.find_elements(
                "css selector",
                ".shareholding_tab li",
            )
        )

        if len(tabs) < 3:
            return

        # -----------------------------------------------------
        # Substantial Shareholders
        # -----------------------------------------------------

        self.browser.driver.execute_script(
            "arguments[0].click();",
            tabs[2],
        )

        time.sleep(3)

        shareholders_html = (
            self.browser.get_response_body(
                "NJhistoryOfMajorShareHolder"
            )
        )

        if shareholders_html:
            result[
                "substantial_shareholders"
            ] = (
                self._parse_substantial_shareholders(
                    shareholders_html
                )
            )

    def _parse_foreign_ownership(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        labels = self.LABELS[
            self.language
        ]

        section = soup.select_one(
            "div.foreign_ownership"
        )

        if section is None:
            return {}

        result = {
            "maximum_limit": None,
            "actual": None,
            "strategic_investors_actual": None,
            "last_updated": None,
        }

        items = section.select(
            ".total_foreign_ownership > ul > li"
        )

        if len(items) >= 1:
            total = items[0]

            maximum = total.select_one(
                ".max_limit strong"
            )

            actual = total.select_one(
                ".actual strong"
            )

            if maximum:
                result[
                    "maximum_limit"
                ] = self._clean_value(
                    maximum.get_text(
                        " ",
                        strip=True,
                    )
                )

            if actual:
                result[
                    "actual"
                ] = self._clean_value(
                    actual.get_text(
                        " ",
                        strip=True,
                    )
                )

        if len(items) >= 2:
            strategic = items[1]

            actual = strategic.select_one(
                ".max_limit strong"
            )

            if actual:
                result[
                    "strategic_investors_actual"
                ] = self._clean_value(
                    actual.get_text(
                        " ",
                        strip=True,
                    )
                )

        last_update = section.select_one(
            ".last_update"
        )

        if last_update:
            last_update_text = (
                self._clean_value(
                    last_update.get_text(
                        " ",
                        strip=True,
                    )
                )
            )

            if last_update_text:
                if self.language == "en":
                    last_update_text = re.sub(
                        r"^Last updated on\s*:?\s*",
                        "",
                        last_update_text,
                        flags=re.IGNORECASE,
                    )
                else:
                    last_update_text = re.sub(
                        r"^(?:آخر تحديث|تاريخ\s+آخر\s+تحديث)\s*:?\s*",
                        "",
                        last_update_text,
                    )

                result[
                    "last_updated"
                ] = last_update_text.strip()

        return result

    @staticmethod
    def _parse_substantial_shareholders(
        html: str,
    ) -> dict:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        result = {
            "substantial_shareholders": [],
            "shareholders_subject_to_lock_up": [],
        }

        def parse_table(
            table_id: str,
        ):
            table = soup.find(
                "table",
                id=table_id,
            )

            if table is None:
                return []

            shareholders = []

            for row in table.select(
                "tr"
            ):
                cells = row.find_all(
                    "td"
                )

                if len(cells) < 5:
                    continue

                if "no-records-found" in (
                    row.get(
                        "class",
                        [],
                    )
                ):
                    continue

                values = [
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                    for cell in cells
                ]

                if not any(values):
                    continue

                shareholders.append(
                    {
                        "trading_date": values[0],
                        "shareholder": values[1],
                        "total_shares_held_trading_day": values[2],
                        "total_shares_held_prev_trading_day": values[3],
                        "total_shares_change": values[4],
                    }
                )

            return shareholders

        result[
            "substantial_shareholders"
        ] = parse_table(
            "majorShareHoldersTable"
        )

        result[
            "shareholders_subject_to_lock_up"
        ] = parse_table(
            "majorShareHoldersTableLock"
        )

        return result

    # ---------------------------------------------------------
    # Context manager
    # ---------------------------------------------------------

    def close(self):
        self.browser.close()

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        self.close()