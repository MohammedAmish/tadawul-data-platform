from __future__ import annotations

import json
import re
import time

from urllib.parse import (
    parse_qsl,
    urlencode,
    urlparse,
    urlunparse,
)

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from tadawul.scraper.browser import TadawulBrowser


class CefScraper:
    SUPPORTED_LANGUAGES = {"en", "ar"}

    CEF_MARKET_WATCH_PAGE = (
        "/wps/portal/saudiexchange/ourmarkets/"
        "funds-market-watch/cefs"
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
            "financials_tab": (
                "Detailed Reports and Statements"
            ),
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
            "popup_bd_session_start": "BD Session Start",
            "popup_designation": "Designation",
            "popup_bd_session_end": "BD Session End",
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
                "التقارير و القوائم المالية المفصلة"
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
            "authorized_capital": "authorized_capital",
            "no_of_units": "number_of_units",
            "paid_capital": "paid_capital",
            "par_value_unit": "par_value_per_unit",
            "paid_up_value_unit": "paid_up_value_per_unit",
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

        self.browser = TadawulBrowser(
            headless=headless
        )

        self.browser.set_locale(language)

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

    def _text(
        self,
        element,
    ) -> str | None:
        if element is None:
            return None

        value = element.get_text(
            " ",
            strip=True,
        )

        return value or None

    def _clean_value(
        self,
        value: str | None,
    ):
        if value is None:
            return None

        value = value.replace(
            "\xa0",
            " ",
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    def _normalise_label(
        self,
        value: str | None,
    ) -> str | None:
        value = self._clean_value(value)

        if value is None:
            return None

        value = re.sub(
            r"\s*:\s*$",
            "",
            value,
        )

        return value.strip()

    def _get_label_value(
        self,
        container,
        label: str,
    ):
        target_label = self._normalise_label(label)

        heading = container.find(
            lambda tag: (
                tag.name in {
                    "h2",
                    "h4",
                    "strong",
                }
                and self._normalise_label(
                    self._text(tag)
                )
                == target_label
            )
        )

        if heading is None:
            return None

        value = heading.find_next_sibling()

        while value is not None:
            text = self._clean_value(
                self._text(value)
            )

            if text:
                return text

            value = value.find_next_sibling()

        return None

    def _normalise_key(
        self,
        value: str,
    ):
        value = value.strip().lower()

        value = re.sub(
            r"[^a-z0-9]+",
            "_",
            value,
        )

        return value.strip("_")

    def get_all_cefs(self):
        market_watch_url = (
            self.browser.BASE_URL
            + self.CEF_MARKET_WATCH_PAGE
        )

        self.browser.open(
            self._set_url_locale(
                market_watch_url
            ),
            wait_seconds=5,
        )

        soup = BeautifulSoup(
            self.browser.driver.page_source,
            "html.parser",
        )

        table = soup.select_one(
            "#cefMarketWatchTable"
        )

        if table is None:
            raise RuntimeError(
                "CEF market-watch table was not found"
            )

        cefs = []

        for link in table.select(
            'a[href*="company-profile-main"]'
        ):
            name = self._clean_value(
                self._text(link)
            )

            href = link.get("href")

            if not href:
                continue

            url = (
                href
                if href.startswith("http")
                else self.browser.BASE_URL + href
            )

            cefs.append(
                {
                    "name": name,
                    "url": self._set_url_locale(
                        url
                    ),
                }
            )

        if not cefs:
            raise RuntimeError(
                "No CEFs were found"
            )

        return cefs

    def _parse_fund_profile(
        self,
        soup,
    ):
        section = soup.select_one(
            "div.fundInfo"
        )

        if section is None:
            return {}

        labels = self.LABELS[self.language]

        result = {
            "fund_overview": None,
            "managed_assets": None,
            "terms_and_conditions": None,
            "units_profile": {},
            "investment_limits": None,
        }

        # Fund Overview
        overview_heading = section.find(
            lambda tag: (
                tag.name == "strong"
                and self._normalise_label(
                    self._text(tag)
                )
                == self._normalise_label(
                    labels["fund_overview"]
                )
            )
        )

        if overview_heading:
            heading_paragraph = (
                overview_heading.find_parent("p")
            )

            if heading_paragraph:
                value_paragraph = (
                    heading_paragraph.find_next_sibling(
                        "p"
                    )
                )

                if value_paragraph:
                    result["fund_overview"] = (
                        self._clean_value(
                            self._text(
                                value_paragraph
                            )
                        )
                    )

        # Managed Assets
        managed_heading = section.find(
            lambda tag: (
                tag.name == "strong"
                and self._normalise_label(
                    self._text(tag)
                )
                == self._normalise_label(
                    labels["managed_assets"]
                )
            )
        )

        if managed_heading:
            heading_paragraph = (
                managed_heading.find_parent("p")
            )

            if heading_paragraph:
                value_paragraph = (
                    heading_paragraph.find_next_sibling(
                        "p"
                    )
                )

                if value_paragraph:
                    result["managed_assets"] = (
                        self._clean_value(
                            self._text(
                                value_paragraph
                            )
                        )
                    )

        # Terms and Conditions
        terms_heading = section.find(
            lambda tag: (
                tag.name == "strong"
                and self._normalise_label(
                    self._text(tag)
                )
                == self._normalise_label(
                    labels["terms_and_conditions"]
                )
            )
        )

        if terms_heading:
            heading_paragraph = (
                terms_heading.find_parent("p")
            )

            if heading_paragraph:
                value_paragraph = (
                    heading_paragraph.find_next_sibling(
                        "p"
                    )
                )

                if value_paragraph:
                    link = value_paragraph.find(
                        "a"
                    )

                    if link:
                        result[
                            "terms_and_conditions"
                        ] = {
                            "text": self._clean_value(
                                self._text(link)
                            ),
                            "url": link.get(
                                "href"
                            ),
                        }

        # Units Profile
        units_heading = section.find(
            lambda tag: (
                tag.name == "strong"
                and self._normalise_label(
                    self._text(tag)
                )
                == self._normalise_label(
                    labels["units_profile"]
                )
            )
        )

        if units_heading:
            units_heading_paragraph = (
                units_heading.find_parent("p")
            )

            if units_heading_paragraph:
                units_container = (
                    units_heading_paragraph.find_next_sibling(
                        "div"
                    )
                )

                if units_container:
                    for item in units_container.select(
                        "ul > li"
                    ):
                        label_element = item.find(
                            "span"
                        )

                        value_element = item.find(
                            "strong"
                        )

                        if (
                            label_element is None
                            or value_element is None
                        ):
                            continue

                        label = self._clean_value(
                            self._text(
                                label_element
                            )
                        )

                        value = self._clean_value(
                            self._text(
                                value_element
                            )
                        )

                        if not label or value is None:
                            continue

                        label = re.sub(
                            r"\s*\(\s*\^\s*\)\s*",
                            "",
                            label,
                        )

                        key = None

                        if self.language == "en":
                            normalised = (
                                self._normalise_key(
                                    label
                                )
                            )

                            key = {
                                "authorized_capital": (
                                    "authorized_capital"
                                ),
                                "no_of_units": (
                                    "number_of_units"
                                ),
                                "paid_capital": (
                                    "paid_capital"
                                ),
                                "par_value_unit": (
                                    "par_value_per_unit"
                                ),
                                "paid_up_value_unit": (
                                    "paid_up_value_per_unit"
                                ),
                            }.get(
                                normalised,
                                normalised,
                            )

                        else:
                            for (
                                arabic_label,
                                mapped_key,
                            ) in self.UNIT_KEYS[
                                "ar"
                            ].items():
                                if arabic_label in label:
                                    key = mapped_key
                                    break

                            if key is None:
                                key = self._normalise_key(
                                    label
                                )

                        result[
                            "units_profile"
                        ][key] = value

                    last_update = units_container.find(
                        lambda tag: (
                            tag.name == "p"
                            and labels["last_update"]
                            in self._text(tag)
                        )
                    )

                    if last_update:
                        if self.language == "en":
                            pattern = (
                                r"Last Update"
                                r"\s*:?\s*(.+)"
                            )
                        else:
                            pattern = (
                                r"آخر تحديث"
                                r"\s*:?\s*(.+)"
                            )

                        match = re.search(
                            pattern,
                            self._text(
                                last_update
                            ),
                            flags=re.IGNORECASE,
                        )

                        if match:
                            result[
                                "units_profile"
                            ]["last_update"] = (
                                self._clean_value(
                                    match.group(1)
                                )
                            )

        # Investment Limits
        investment_heading = section.find(
            lambda tag: (
                tag.name == "h2"
                and self._normalise_label(
                    self._text(tag)
                )
                == self._normalise_label(
                    labels["investment_limits"]
                )
            )
        )

        if investment_heading:
            heading_paragraph = (
                investment_heading.find_parent("p")
            )

            if heading_paragraph:
                value_paragraph = (
                    heading_paragraph.find_next_sibling(
                        "p"
                    )
                )

                if value_paragraph:
                    result[
                        "investment_limits"
                    ] = self._clean_value(
                        self._text(
                            value_paragraph
                        )
                    )

        return result

    def _parse_fund_details(
        self,
        soup,
    ):
        section = soup.select_one(
            "div.company_management_tab_dtl"
        )

        if section is None:
            return {}

        labels = self.LABELS[self.language]

        label_keys = [
            (
                "date_established",
                labels["date_established"],
            ),
            (
                "financial_year_end",
                labels["financial_year_end"],
            ),
            (
                "listing_date",
                labels["listing_date"],
            ),
            (
                "external_auditors",
                labels["external_auditors"],
            ),
            (
                "isin_code",
                labels["isin_code"],
            ),
            (
                "number_of_employees",
                labels["number_of_employees"],
            ),
        ]

        result = {}

        for key, label in label_keys:
            result[key] = self._get_label_value(
                section,
                label,
            )

        return result

    def _parse_management(
        self,
        soup,
    ):
        sections = soup.select(
            "div.company_management_tab_dtl"
        )

        if len(sections) < 2:
            return {
                "fund_chairman": [],
                "fund_board_of_directors": [],
            }

        section = sections[1]

        labels = self.LABELS[self.language]

        result = {
            "fund_chairman": [],
            "fund_board_of_directors": [],
        }

        current_group = None

        for li in section.select("ul > li"):
            heading = li.find("h4")

            if heading:
                heading_text = self._clean_value(
                    self._text(heading)
                )

                if (
                    self._normalise_label(
                        heading_text
                    )
                    == self._normalise_label(
                        labels["fund_chairman"]
                    )
                ):
                    current_group = (
                        "fund_chairman"
                    )

                elif (
                    self._normalise_label(
                        heading_text
                    )
                    == self._normalise_label(
                        labels[
                            "fund_board_of_directors"
                        ]
                    )
                ):
                    current_group = (
                        "fund_board_of_directors"
                    )

                else:
                    current_group = None

            if current_group is None:
                continue

            people = li.select(
                "strong.namePopup"
            )

            for person in people:
                name = self._clean_value(
                    self._text(person)
                )

                if not name:
                    continue

                entry = {
                    "name": name,
                    "designation": None,
                    "classification": None,
                    "bd_session_start": None,
                    "bd_session_end": None,
                }

                # Classification shown directly
                # next to the person's name.
                person_p = person.find_parent("p")

                if person_p:
                    parts = list(
                        person_p.stripped_strings
                    )

                    if len(parts) >= 2:
                        entry[
                            "classification"
                        ] = self._clean_value(
                            parts[-1]
                        )

                # Find the popup belonging to this
                # specific person.
                person_id = person.get("id")

                if person_id:
                    popup_id = person_id.replace(
                        "namePopup_",
                        "namePopupBox_",
                    )

                    popup = soup.find(
                        id=popup_id
                    )

                    if popup:
                        fields = {}

                        for field in popup.select(
                            ".topTxt"
                        ):
                            label = self._normalise_label(
                                self._text(field)
                            )

                            value_element = (
                                field.find_next_sibling(
                                    class_="btmTxt"
                                )
                            )

                            if value_element:
                                value = (
                                    self._clean_value(
                                        self._text(
                                            value_element
                                        )
                                    )
                                )

                                fields[label] = value

                        entry[
                            "bd_session_start"
                        ] = fields.get(
                            self._normalise_label(
                                labels[
                                    "popup_bd_session_start"
                                ]
                            )
                        )

                        entry[
                            "designation"
                        ] = fields.get(
                            self._normalise_label(
                                labels[
                                    "popup_designation"
                                ]
                            )
                        )

                        entry[
                            "bd_session_end"
                        ] = fields.get(
                            self._normalise_label(
                                labels[
                                    "popup_bd_session_end"
                                ]
                            )
                        )

                        entry[
                            "classification"
                        ] = (
                            fields.get(
                                self._normalise_label(
                                    labels[
                                        "popup_classification"
                                    ]
                                )
                            )
                            or entry[
                                "classification"
                            ]
                        )

                result[
                    current_group
                ].append(entry)

        return result

    def _parse_investor_relations(
        self,
        soup,
    ):
        section = soup.select_one(
            "div.investor_relations"
        )

        if section is None:
            return {}

        labels = self.LABELS[self.language]

        result = {
            "contact_name": None,
            "company_address": None,
            "telephone": None,
            "fax": None,
            "email": None,
            "company_website": None,
        }

        for heading in section.select("h4"):
            label = self._normalise_label(
                self._text(heading)
            )

            if not label:
                continue

            value = heading.find_next_sibling(
                "p"
            )

            if value is None:
                continue

            if (
                label
                == self._normalise_label(
                    labels["contact_name"]
                )
            ):
                result["contact_name"] = (
                    self._clean_value(
                        self._text(value)
                    )
                )

            elif (
                label
                == self._normalise_label(
                    labels["company_address"]
                )
            ):
                result["company_address"] = (
                    self._clean_value(
                        self._text(value)
                    )
                )

            elif (
                label
                == self._normalise_label(
                    labels["contact_details"]
                )
            ):
                text = self._clean_value(
                    self._text(value)
                )

                if self.language == "en":
                    telephone_pattern = (
                        r"Telephone\s*:?\s*([0-9]+)"
                    )
                    fax_pattern = (
                        r"Fax\s*:?\s*([0-9]+)"
                    )
                else:
                    telephone_pattern = (
                        r"(?:الهاتف|هاتف)"
                        r"\s*:?\s*([0-9]+)"
                    )
                    fax_pattern = (
                        r"فاكس"
                        r"\s*:?\s*([0-9]+)"
                    )

                telephone = re.search(
                    telephone_pattern,
                    text,
                    flags=re.IGNORECASE,
                )

                fax = re.search(
                    fax_pattern,
                    text,
                    flags=re.IGNORECASE,
                )

                email = value.select_one(
                    'a[href^="mailto:"]'
                )

                if telephone:
                    result["telephone"] = (
                        telephone.group(1)
                    )

                if fax:
                    result["fax"] = (
                        fax.group(1)
                    )

                if email:
                    email_href = email.get(
                        "href",
                        "",
                    )

                    if email_href.lower().startswith(
                        "mailto:"
                    ):
                        result["email"] = (
                            email_href[
                                len("mailto:"):
                            ].strip()
                        )
                    else:
                        result["email"] = (
                            self._clean_value(
                                self._text(email)
                            )
                        )

            elif (
                label
                == self._normalise_label(
                    labels["company_website"]
                )
            ):
                link = value.find("a")

                if link:
                    result[
                        "company_website"
                    ] = self._clean_value(
                        self._text(link)
                    )

        return result

    def _parse_foreign_ownership(
        self,
        soup,
    ):
        section = soup.select_one(
            "div.foreign_ownership"
        )

        if section is None:
            return {}

        result = {
            "maximum_limit": None,
            "actual": None,
            "strategic_investors_actual": None,
        }

        items = section.select(
            ".total_foreign_ownership > ul > li"
        )

        # Total foreign ownership
        if len(items) >= 1:
            total = items[0]

            maximum_limit = total.select_one(
                ".max_limit strong"
            )

            actual = total.select_one(
                ".actual strong"
            )

            if maximum_limit:
                result[
                    "maximum_limit"
                ] = self._clean_value(
                    self._text(
                        maximum_limit
                    )
                )

            if actual:
                result["actual"] = (
                    self._clean_value(
                        self._text(actual)
                    )
                )

        # Foreign strategic investors
        if len(items) >= 2:
            strategic = items[1]

            strategic_actual = strategic.select_one(
                ".max_limit strong"
            )

            if strategic_actual:
                result[
                    "strategic_investors_actual"
                ] = self._clean_value(
                    self._text(
                        strategic_actual
                    )
                )

        return result

    def _get_dynamic_response(
        self,
        endpoint,
        click_text,
    ):
        driver = self.browser.driver

        element = None

        for candidate in driver.find_elements(
            By.XPATH,
            "//a | //li | //button",
        ):
            if not candidate.is_displayed():
                continue

            text = candidate.text.strip()

            if text == click_text:
                element = candidate
                break

        if element is None:
            return None

        driver.get_log("performance")

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            element,
        )

        time.sleep(0.5)

        driver.execute_script(
            "arguments[0].click();",
            element,
        )

        deadline = time.time() + 10

        while time.time() < deadline:
            for entry in driver.get_log(
                "performance"
            ):
                message = json.loads(
                    entry["message"]
                )["message"]

                if message["method"] != (
                    "Network.responseReceived"
                ):
                    continue

                response = message[
                    "params"
                ]["response"]

                url = response["url"]

                if endpoint not in url:
                    continue

                request_id = message[
                    "params"
                ]["requestId"]

                try:
                    body = driver.execute_cdp_cmd(
                        "Network.getResponseBody",
                        {
                            "requestId": request_id
                        },
                    )

                    return body["body"]

                except Exception:
                    continue

            time.sleep(0.2)

        return None

    def _parse_financials(
        self,
        html: str | None,
    ) -> dict:
        if not html:
            return {
                "reports": {}
            }

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        table = soup.select_one("table")

        if not table:
            return {
                "reports": {}
            }

        headers = []

        for th in table.select(
            "thead th"
        ):
            text = self._clean_value(
                th.get_text(
                    " ",
                    strip=True,
                )
            )

            if text:
                headers.append(text)

        years = [
            header
            for header in headers
            if re.fullmatch(
                r"\d{4}",
                header,
            )
        ]

        reports = {}

        for row in table.select(
            "tbody tr"
        ):
            cells = row.find_all("td")

            if not cells:
                continue

            period = self._clean_value(
                cells[0].get_text(
                    " ",
                    strip=True,
                )
            )

            if not period:
                continue

            period_data = {}

            for index, cell in enumerate(
                cells[1:]
            ):
                if index >= len(years):
                    break

                year = years[index]

                link = cell.select_one(
                    "a[href]"
                )

                url = None

                if link:
                    url = link.get("href")

                date = None

                date_element = cell.find(
                    "p"
                )

                if date_element:
                    date = self._clean_value(
                        date_element.get_text(
                            " ",
                            strip=True,
                        )
                    )

                if date == "-":
                    date = None

                period_data[year] = {
                    "date": date,
                    "url": url,
                }

            reports[period] = period_data

        return {
            "reports": reports,
        }

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

        def parse_table(table_id: str) -> list[dict]:
            table = soup.find(
                "table",
                id=table_id,
            )

            if table is None:
                return []

            shareholders = []

            for row in table.select("tbody tr"):
                cells = row.find_all("td")

                if len(cells) < 5:
                    continue

                if "no-records-found" in row.get(
                    "class",
                    [],
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

        result["substantial_shareholders"] = parse_table(
            "majorShareHoldersTable"
        )

        result["shareholders_subject_to_lock_up"] = parse_table(
            "majorShareHoldersTableLock"
        )

        return result

    def scrape(
        self,
        url: str,
    ):
        url = self._set_url_locale(url)

        self.browser.open(
            url,
            wait_seconds=5,
        )

        soup = BeautifulSoup(
            self.browser.driver.page_source,
            "html.parser",
        )

        symbol = None
        cef_name = None
        market = None
        fund_type = None

        symbol_element = soup.select_one(
            "div.saudiCable.stats_overview "
            "div.price_name div.price"
        )

        if symbol_element:
            symbol = self._clean_value(
                self._text(symbol_element)
            )

        name_element = soup.select_one(
            "div.saudiCable.stats_overview "
            "div.price_name div.name"
        )

        if name_element:
            cef_name = self._clean_value(
                self._text(name_element)
            )

        # Market and fund type
        market_capital = soup.select_one(
            "div.market_capital"
        )

        if market_capital:
            items = market_capital.select(
                "li"
            )

            if len(items) >= 1:
                market = self._clean_value(
                    self._text(items[0])
                )

            if len(items) >= 2:
                fund_type = self._clean_value(
                    self._text(items[1])
                )

        result = {
            "symbol": symbol,
            "cef_name": cef_name,
            "language": self.language,
            "market": market,
            "fund_type": fund_type,
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
            "foreign_ownership": (
                self._parse_foreign_ownership(
                    soup
                )
            ),
            "financials": {},
            "substantial_shareholders": {},
        }

        labels = self.LABELS[self.language]

        # Financials
        financial_body = (
            self._get_dynamic_response(
                "NJstatementsTabData",
                labels["financials_tab"],
            )
        )

        result["financials"] = (
            self._parse_financials(
                financial_body
            )
        )

        # Substantial shareholders
        shareholder_body = (
            self._get_dynamic_response(
                "NJhistoryOfMajorShareHolder",
                labels[
                    "substantial_shareholders_tab"
                ],
            )
        )

        result[
            "substantial_shareholders"
        ] = self._parse_substantial_shareholders(
            shareholder_body
        )

        return result

    def close(self):
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