from __future__ import annotations

import json
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from tadawul.scraper.browser import TadawulBrowser


class CompanyScraper:
    SUPPORTED_LANGUAGES = {"en", "ar"}

    STATEMENT_TYPES = {
        0: "balance_sheet",
        1: "statement_of_income",
        2: "cash_flows",
    }

    LABELS = {
        "en": {
            "main_market": "Main Market",
            "common_shares": "Common Shares",
            "company_overview": "Company overview",
            "company_history": "Company History",
            "company_bylaws": "Company Bylaws",
            "subsidiary_name": "Name of Subsidiary",
            "equity_profile": "Equity Profile",
            "foreign_ownership": "Foreign Ownership",
            "substantial_shareholders": "Substantial Shareholders",
            "senior_executives": "Senior Executives",
            "balance_sheet": "Balance Sheet",
            "statement_of_income": "Statement of Income",
            "cash_flows": "Cash Flows",
            "company_details": "Company Details",
            "date_established": "Date Established",
            "financial_year_end": "Financial Year End",
            "listing_date": "Listing Date",
            "external_auditors": "External Auditors",
            "isin_code": "ISIN CODE",
            "number_of_employees": "Number of Employees",
            "contact_name": "Contact Name:",
            "company_address": "Company Address:",
            "contact_details": "Contact Details:",
            "company_website": "Company Website:",
            "add_to_watchlist": "Add To Watchlist",
        },
        "ar": {
            "main_market": "السوق الرئيسية",
            "common_shares": "أسهم عادية",
            "company_overview": "نبذة عن نشاط الشركة",
            "company_history": "نبذة عن تاريخ الشركة",
            "company_bylaws": "النظام الأساسي للشركة",
            "subsidiary_name": "اسم الشركة التابعة",
            "equity_profile": "ملف الأسهم",
            "foreign_ownership": "الملكية الأجنبية",
            "substantial_shareholders": "المساهمون الكبار",
            "senior_executives": "كبار التنفيذيين",
            "balance_sheet": "قائمة المركز المالي",
            "statement_of_income": "قائمة الدخل",
            "cash_flows": "قائمة التدفقات النقدية",
            "company_details": "تفاصيل الشركة",
            "date_established": "تاريخ التأسيس",
            "financial_year_end": "نهاية السنة المالية",
            "listing_date": "تاريخ الادراج",
            "external_auditors": "مراجعي الحسابات",
            "isin_code": "الرمز الدولي",
            "number_of_employees": "عدد الموظفين",
            "contact_name": "اسم ضابط الاتصال",
            "company_address": "عنوان الشركة",
            "contact_details": "بيانات الإتصال",
            "company_website": "موقع الشركة:",
            "add_to_watchlist": "إضافة إلى قائمة المتابعة",
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

    @property
    def labels(self) -> dict[str, str]:
        return self.LABELS[self.language]

    def scrape(self, symbol: str) -> dict:
        with TadawulBrowser(
            headless=self.headless
        ) as browser:

            browser.set_locale(self.language)

            company = browser.get_company(symbol)

            company_url = company.get("link")

            if not company_url:
                raise RuntimeError(
                    f"Link for company {symbol} was not found"
                )

            if company_url.startswith("/"):
                company_url = (
                    browser.BASE_URL + company_url
                )

            browser.open(
                company_url,
                wait_seconds=10,
            )

            driver = browser.driver

            company_name = company.get(
                "companyDisplay"
            )

            result = {
                "symbol": symbol,
                "company_name": company_name,
                "language": self.language,
                "market": None,
                "sector": None,
                "shares_type": None,
                "company_profile": {},
                "subsidiaries": [],
                "company_details": {},
                "management_team": {
                    "board_of_directors": [],
                    "senior_executives": [],
                },
                "financial_statements_and_reports": [],
                "board_of_directors_shareholding": [],
                "foreign_ownership": None,
                "substantial_shareholders": {
                    "substantial_shareholders": [],
                    "shareholders_subject_to_lock_up": [],
                },
                "financial_information": {
                    "balance_sheet": [],
                    "statement_of_income": [],
                    "cash_flows": [],
                },
                "balance_sheet": [],
                "statement_of_income": [],
                "cash_flows": [],
            }

            _, sector = (
                self._get_market_and_sector(driver)
            )

            market_type = browser.servlet.get_company(
                symbol
            )["market_type"]

            if market_type == "M":
                result["market"] = (
                    "Main Market"
                    if self.language == "en"
                    else "السوق الرئيسية"
                )
            elif market_type == "S":
                result["market"] = (
                    "Nomu - Parallel Market"
                    if self.language == "en"
                    else "نمو – السوق الموازية"
                )
            else:
                result["market"] = None

            result["sector"] = sector

            result["shares_type"] = self._get_exact_text(
                driver,
                self.labels["common_shares"],
            )

            result["company_profile"] = (
                self._get_company_profile(driver)
            )

            result["subsidiaries"] = (
                self._get_subsidiaries(driver)
            )

            result["company_details"] = (
                self._get_company_details(driver)
            )

            result["management_team"] = (
                self._get_management_team(driver)
            )

            result["financial_information"] = (
                self._get_financial_information(
                    driver
                )
            )
            
            result["board_of_directors_shareholding"] = (
                self._get_board_of_directors_shareholding(
                    driver
                )
            )

            result["financial_statements_and_reports"] = (
                self._get_financial_statements_and_reports(
                    driver,
                    symbol,
                )
            )

            result["foreign_ownership"] = (
                self._get_foreign_ownership(
                    driver,
                    symbol,
                )
            )

            result["substantial_shareholders"] = (
                self._get_substantial_shareholders(
                    driver,
                    symbol,
                )
            )

            self._open_financial_information(
                driver
            )

            for statement_type, key in (
                self.STATEMENT_TYPES.items()
            ):
                records = self._get_statement(
                    driver,
                    symbol,
                    statement_type,
                )

                result[key] = records

        return result

    @staticmethod
    def _get_exact_text(
        driver,
        text: str,
    ) -> str | None:
        elements = driver.find_elements(
            By.XPATH,
            f"//*[normalize-space()='{text}']",
        )

        for element in elements:
            if element.is_displayed():
                value = element.text.strip()

                if value:
                    return value

        return None

    def _get_market_and_sector(
        self,
        driver,
    ) -> tuple[str | None, str | None]:
        market_elements = driver.find_elements(
            By.XPATH,
            f"//li[normalize-space()="
            f"'{self.labels['main_market']}']",
        )

        visible_markets = [
            element
            for element in market_elements
            if element.is_displayed()
        ]

        if not visible_markets:
            return None, None

        market = visible_markets[0]

        items = market.find_elements(
            By.XPATH,
            "./..//li",
        )

        values = [
            item.text.strip()
            for item in items
            if item.text.strip()
        ]

        if len(values) >= 2:
            return values[0], values[1]

        return None, None

    def _get_company_profile(
        self,
        driver,
    ) -> dict:
        containers = driver.find_elements(
            By.CSS_SELECTOR,
            "div.fundInfo",
        )

        visible_containers = [
            container
            for container in containers
            if container.is_displayed()
        ]

        if not visible_containers:
            return {}

        container = visible_containers[0]

        paragraphs = container.find_elements(
            By.TAG_NAME,
            "p",
        )

        profile = {}

        for paragraph in paragraphs:
            text = paragraph.text.strip()

            if (
                text
                == self.labels["company_overview"]
            ):
                next_paragraphs = paragraph.find_elements(
                    By.XPATH,
                    "following-sibling::p[1]",
                )

                if next_paragraphs:
                    profile["company_overview"] = (
                        next_paragraphs[0]
                        .text
                        .strip()
                    )

            elif (
                text
                == self.labels["company_history"]
            ):
                next_paragraphs = paragraph.find_elements(
                    By.XPATH,
                    "following-sibling::p[1]",
                )

                if next_paragraphs:
                    profile["company_history"] = (
                        next_paragraphs[0]
                        .text
                        .strip()
                    )

            elif (
                text
                == self.labels["company_bylaws"]
            ):
                links = paragraph.find_elements(
                    By.XPATH,
                    "following-sibling::p[1]//a",
                )

                if links:
                    profile["company_bylaws_url"] = (
                        links[0]
                        .get_attribute("href")
                    )

        equity_elements = container.find_elements(
            By.XPATH,
            ".//p[strong[normalize-space()="
            f"'{self.labels['equity_profile']}'"
            "]]"
            "/following-sibling::div"
            "[contains(@class, 'inspectionBox')][1]",
        )

        if equity_elements:
            equity = equity_elements[0]

            equity_fields = [
                "authorized_capital",
                "total_issued_shares",
                "paid_up_capital",
                "nominal_value_per_unit",
                "paid_value_per_unit",
            ]

            items = equity.find_elements(
                By.CSS_SELECTOR,
                "li",
            )

            for index, item in enumerate(items):
                if index >= len(equity_fields):
                    break

                spans = item.find_elements(
                    By.TAG_NAME,
                    "span",
                )

                strongs = item.find_elements(
                    By.TAG_NAME,
                    "strong",
                )

                if not spans or not strongs:
                    continue

                value = strongs[0].text.strip()

                profile[equity_fields[index]] = value

        return profile

    def _get_subsidiaries(
        self,
        driver,
    ) -> list[dict]:
        tables = driver.find_elements(
            By.XPATH,
            "//table[.//th[contains("
            "translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
            "'abcdefghijklmnopqrstuvwxyz'), "
            f"'{self.labels['subsidiary_name'].lower()}'"
            ")]]",
        )

        visible_tables = [
            table
            for table in tables
            if table.is_displayed()
        ]

        if not visible_tables:
            return []

        table = visible_tables[0]

        rows = table.find_elements(
            By.CSS_SELECTOR,
            "tbody tr",
        )

        subsidiaries = []

        for row in rows:
            cells = row.find_elements(
                By.TAG_NAME,
                "td",
            )

            if len(cells) < 5:
                continue

            values = [
                cell.text.strip()
                for cell in cells
            ]

            if not any(values):
                continue

            name = values[0]

            if not name:
                continue

            ownership = values[1]

            try:
                ownership_percentage = float(
                    ownership
                    .replace("%", "")
                    .strip()
                )
            except ValueError:
                ownership_percentage = None

            subsidiaries.append(
                {
                    "name": name,
                    "ownership_percentage": (
                        ownership_percentage
                    ),
                    "main_business": (
                        values[2] or None
                    ),
                    "location": (
                        values[3] or None
                    ),
                    "country": (
                        values[4] or None
                    ),
                }
            )

        return subsidiaries

    def _get_company_details(
        self,
        driver,
    ) -> dict:
        containers = driver.find_elements(
            By.CSS_SELECTOR,
            "div.companyProfile",
        )

        visible_containers = [
            container
            for container in containers
            if container.is_displayed()
        ]

        details = {
            "date_established": None,
            "financial_year_end": None,
            "listing_date": None,
            "external_auditors": None,
            "isin_code": None,
            "number_of_employees": None,
            "investor_relations": {},
        }

        if not visible_containers:
            return details

        container = visible_containers[0]

        text = container.text.strip()

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        fields = {
            self.labels["date_established"]:
                "date_established",
            self.labels["financial_year_end"]:
                "financial_year_end",
            self.labels["listing_date"]:
                "listing_date",
            self.labels["external_auditors"]:
                "external_auditors",
            self.labels["isin_code"]:
                "isin_code",
            self.labels["number_of_employees"]:
                "number_of_employees",
        }

        for index, line in enumerate(lines):
            if (
                line in fields
                and index + 1 < len(lines)
            ):
                details[
                    fields[line]
                ] = lines[index + 1]

        investor_relations = (
            details["investor_relations"]
        )

        for index, line in enumerate(lines):
            if (
                line
                == self.labels["contact_name"]
                and index + 1 < len(lines)
            ):
                investor_relations[
                    "contact_name"
                ] = lines[index + 1]

            elif (
                line
                == self.labels["company_address"]
                and index + 1 < len(lines)
            ):
                investor_relations[
                    "company_address"
                ] = lines[index + 1]

            elif (
                line
                == self.labels["contact_details"]
            ):
                contact_details = []

                for value in lines[index + 1:]:
                    if value in {
                        self.labels[
                            "company_website"
                        ],
                        self.labels[
                            "add_to_watchlist"
                        ],
                    }:
                        break

                    contact_details.append(
                        value
                    )

                investor_relations[
                    "contact_details"
                ] = contact_details

            elif (
                line
                == self.labels["company_website"]
                and index + 1 < len(lines)
            ):
                investor_relations[
                    "company_website"
                ] = lines[index + 1]

        return details

    def _get_management_team(
        self,
        driver,
    ) -> dict:
        sections = driver.find_elements(
            By.CSS_SELECTOR,
            "div.company_management_tab_dtl",
        )

        if len(sections) < 2:
            return {
                "board_of_directors": [],
                "senior_executives": [],
            }

        management = sections[1]

        board_of_directors = []
        senior_executives = []

        groups = management.find_elements(
            By.XPATH,
            "./div/div/ul/li",
        )

        for group in groups:
            heading_elements = group.find_elements(
                By.TAG_NAME,
                "h4",
            )

            if not heading_elements:
                continue

            heading = (
                heading_elements[0]
                .get_attribute("textContent")
                .strip()
            )

            people = group.find_elements(
                By.XPATH,
                "./p[strong[contains("
                "@class, 'namePopup')]]",
            )

            for person in people:
                name_element = person.find_element(
                    By.CSS_SELECTOR,
                    "strong.namePopup",
                )

                name = (
                    name_element
                    .get_attribute(
                        "textContent"
                    )
                    .strip()
                )

                person_data = {
                    "name": name,
                    "role": None,
                    "classification": None,
                    "bd_session_start": None,
                    "bd_session_end": None,
                    "designation": None,
                }

                person_text = (
                    person
                    .get_attribute(
                        "textContent"
                    )
                    .strip()
                )

                if person_text.startswith(name):
                    role = person_text[
                        len(name):
                    ].strip()

                    if role:
                        person_data[
                            "role"
                        ] = role

                popup_id = (
                    name_element
                    .get_attribute("id")
                )

                if popup_id:
                    popup_id = popup_id.replace(
                        "namePopup_",
                        "namePopupBox_",
                    )

                    popups = driver.find_elements(
                        By.ID,
                        popup_id,
                    )

                    if popups:
                        popup = popups[0]

                        fields = popup.find_elements(
                            By.CSS_SELECTOR,
                            ".topTxt, .btmTxt",
                        )

                        for index in range(
                            0,
                            len(fields) - 1,
                            2,
                        ):
                            key = (
                                fields[index]
                                .get_attribute(
                                    "textContent"
                                )
                                .strip()
                            )

                            value = (
                                fields[index + 1]
                                .get_attribute(
                                    "textContent"
                                )
                                .strip()
                            )

                            self._set_management_field(
                                person_data,
                                key,
                                value,
                            )

                if (
                    heading
                    == self.labels[
                        "senior_executives"
                    ]
                ):
                    senior_executives.append(
                        person_data
                    )
                else:
                    board_of_directors.append(
                        person_data
                    )

        return {
            "board_of_directors": (
                board_of_directors
            ),
            "senior_executives": (
                senior_executives
            ),
        }

    def _set_management_field(
        self,
        person_data: dict,
        key: str,
        value: str,
    ) -> None:
        field_map = {
            "en": {
                "BD Session Start":
                    "bd_session_start",
                "BD Session End":
                    "bd_session_end",
                "Designation":
                    "designation",
                "Classification":
                    "classification",
            },
            "ar": {
                "تاريخ بداية دورة المجلس":
                    "bd_session_start",
                "تاريخ نهاية دورة المجلس":
                    "bd_session_end",
                "صفة العضوية":
                    "classification",
                "منصب":
                    "designation",
            },
        }

        output_key = field_map.get(
            self.language,
            {},
        ).get(key)

        if output_key:
            person_data[output_key] = value

    def _get_financial_statements_and_reports(
        self,
        driver,
        symbol: str,
    ) -> list[dict]:
        driver.get_log("performance")

        tabs = driver.find_elements(
            By.ID,
            "finacialStatementAndReports",
        )

        visible_tabs = [
            tab
            for tab in tabs
            if tab.is_displayed()
        ]

        if not visible_tabs:
            return []

        tab = visible_tabs[0]

        driver.execute_script(
            "arguments[0].click();",
            tab,
        )

        deadline = time.time() + 15

        while time.time() < deadline:
            logs = driver.get_log(
                "performance"
            )

            for entry in logs:
                message = json.loads(
                    entry["message"]
                )["message"]

                if (
                    message["method"]
                    != "Network.responseReceived"
                ):
                    continue

                response = message[
                    "params"
                ]["response"]

                response_url = response["url"]

                if (
                    "NJstatementsTabData"
                    not in response_url
                    or "statementType=6"
                    not in response_url
                    or "reportType=0"
                    not in response_url
                    or (
                        f"requestLocale={self.language}"
                        not in response_url
                    )
                    or f"symbol={symbol}"
                    not in response_url
                ):
                    continue

                request_id = message[
                    "params"
                ]["requestId"]

                try:
                    result = driver.execute_cdp_cmd(
                        "Network.getResponseBody",
                        {
                            "requestId": request_id,
                        },
                    )

                    return (
                        self._parse_financial_reports(
                            result["body"]
                        )
                    )

                except Exception:
                    continue

            time.sleep(0.2)

        return []

    @staticmethod
    def _parse_financial_reports(
        html: str,
    ) -> list[dict]:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        table = soup.find("table")

        if table is None:
            return []

        rows = table.find_all("tr")

        reports = []

        current_section = None
        current_years = []

        for row in rows:
            section_header = row.find(
                "th",
                attrs={"colspan": True},
            )

            if section_header:
                current_section = (
                    section_header.get_text(
                        " ",
                        strip=True,
                    )
                )

                current_years = []
                continue

            year_headers = row.find_all("th")

            detected_years = []

            for header in year_headers:
                text = header.get_text(
                    " ",
                    strip=True,
                )

                for value in text.split():
                    if (
                        value.isdigit()
                        and len(value) == 4
                        and 2000 <= int(value) <= 2100
                    ):
                        year = int(value)

                        if year not in detected_years:
                            detected_years.append(
                                year
                            )

            if len(detected_years) >= 2:
                current_years = detected_years
                continue

            if (
                not current_section
                or not current_years
            ):
                continue

            cells = row.find_all("td")

            if not cells:
                continue

            period = cells[0].get_text(
                " ",
                strip=True,
            )

            if not period:
                continue

            for index, cell in enumerate(
                cells[1:]
            ):
                if index >= len(current_years):
                    break

                year = current_years[index]

                publication_date = None

                date_element = cell.find("p")

                if date_element:
                    publication_date = (
                        date_element.get_text(
                            " ",
                            strip=True,
                        )
                    )

                links = cell.find_all(
                    "a",
                    href=True,
                )

                for link in links:
                    href = link.get("href")

                    if not href:
                        continue

                    reports.append(
                        {
                            "section": (
                                current_section
                            ),
                            "period": period,
                            "year": year,
                            "publication_date": (
                                publication_date
                            ),
                            "file_type": (
                                CompanyScraper
                                ._get_file_type(
                                    href
                                )
                            ),
                            "file_url": urljoin(
                                TadawulBrowser.BASE_URL,
                                href,
                            ),
                        }
                    )

        return reports
    
    def _get_board_of_directors_shareholding(
        self,
        driver,
    ) -> list[dict]:
        tables = driver.find_elements(
            By.TAG_NAME,
            "table",
        )

        for table in tables:
            headers = table.find_elements(
                By.TAG_NAME,
                "th",
            )

            if len(headers) < 6:
                continue

            header_values = [
                " ".join(
                    header.text.split()
                ).casefold()
                for header in headers
            ]

            if self.language == "en":
                if (
                    header_values[0] != "trading date"
                    or header_values[1] != "shareholders"
                    or header_values[2] != "designation"
                ):
                    continue

            elif self.language == "ar":
                if (
                    header_values[0] != "تاريخ التداول"
                    or header_values[1] != "المساهمون"
                    or header_values[2] != "منصب"
                ):
                    continue

            else:
                continue

            rows = table.find_elements(
                By.TAG_NAME,
                "tr",
            )

            shareholders = []

            for row in rows[1:]:
                cells = row.find_elements(
                    By.TAG_NAME,
                    "td",
                )

                if len(cells) < 6:
                    continue

                values = [
                    cell.text.strip()
                    for cell in cells
                ]

                shareholders.append(
                    {
                        "trading_date": values[0],
                        "shareholder": values[1],
                        "designation": values[2],
                        "total_shares_held_trading_day":
                            values[3],
                        "total_shares_held_prev_trading_day":
                            values[4],
                        "total_shares_change":
                            values[5],
                    }
                )

            return shareholders

        return []

    def _get_foreign_ownership(
        self,
        driver,
        symbol: str,
    ) -> dict | None:
        driver.get_log("performance")

        try:
            deadline = time.time() + 15
            foreign_ownership_tab = None

            while time.time() < deadline:
                elements = driver.find_elements(
                    By.XPATH,
                    "//li[normalize-space()="
                    f"'{self.labels['foreign_ownership']}'"
                    "]",
                )

                visible_elements = [
                    element
                    for element in elements
                    if element.is_displayed()
                ]

                if visible_elements:
                    foreign_ownership_tab = (
                        visible_elements[0]
                    )
                    break

                time.sleep(0.2)

            if foreign_ownership_tab is None:
                return None

            driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    block: 'center',
                    inline: 'center'
                });
                """,
                foreign_ownership_tab,
            )

            driver.get_log("performance")

            driver.execute_script(
                "arguments[0].click();",
                foreign_ownership_tab,
            )

            deadline = time.time() + 15

            while time.time() < deadline:
                logs = driver.get_log(
                    "performance"
                )

                for entry in logs:
                    message = json.loads(
                        entry["message"]
                    )["message"]

                    if (
                        message["method"]
                        != "Network.responseReceived"
                    ):
                        continue

                    response = message[
                        "params"
                    ]["response"]

                    response_url = response["url"]

                    if (
                        "NJforeginOwnerShip"
                        not in response_url
                        or f"symbol={symbol}"
                        not in response_url
                    ):
                        continue

                    request_id = message[
                        "params"
                    ]["requestId"]

                    try:
                        result = (
                            driver.execute_cdp_cmd(
                                "Network.getResponseBody",
                                {
                                    "requestId": request_id,
                                },
                            )
                        )

                        return (
                            self._parse_foreign_ownership(
                                result["body"]
                            )
                        )

                    except Exception:
                        pass

                time.sleep(0.2)

        except Exception:
            pass

        return None

    @staticmethod
    def _parse_foreign_ownership(
        html: str,
    ) -> dict:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        result = {
            "total_foreign_ownership": {
                "maximum_limit_percent": None,
                "actual_percent": None,
            },
            "foreign_strategic_investors_ownership_percent":
                None,
            "last_updated": None,
        }

        container = soup.select_one(
            "div.foreign_ownership"
        )

        if container is None:
            return result

        sections = container.select(
            ".total_foreign_ownership > ul > li"
        )

        if sections:
            values = sections[0].find_all(
                "strong"
            )

            if len(values) >= 2:
                maximum_limit = (
                    values[0].get_text(
                        " ",
                        strip=True,
                    )
                )

                actual = values[1].get_text(
                    " ",
                    strip=True,
                )

                try:
                    result[
                        "total_foreign_ownership"
                    ][
                        "maximum_limit_percent"
                    ] = float(maximum_limit)
                except ValueError:
                    pass

                try:
                    result[
                        "total_foreign_ownership"
                    ][
                        "actual_percent"
                    ] = float(actual)
                except ValueError:
                    pass

        if len(sections) >= 2:
            value = sections[1].find(
                "strong"
            )

            if value:
                value = value.get_text(
                    " ",
                    strip=True,
                )

                try:
                    result[
                        "foreign_strategic_investors_ownership_percent"
                    ] = float(value)
                except ValueError:
                    pass

        last_update = container.select_one(
            ".last_update"
        )

        if last_update:
            text = last_update.get_text(
                " ",
                strip=True,
            )

            if ":" in text:
                result["last_updated"] = (
                    text.split(
                        ":",
                        1,
                    )[1].strip()
                )

        return result

    def _get_substantial_shareholders(
        self,
        driver,
        symbol: str,
    ) -> dict:
        driver.get_log("performance")

        try:
            deadline = time.time() + 15
            substantial_shareholders_tab = None

            while time.time() < deadline:
                elements = driver.find_elements(
                    By.XPATH,
                    "//li[normalize-space()="
                    f"'{self.labels['substantial_shareholders']}'"
                    "]",
                )

                visible_elements = [
                    element
                    for element in elements
                    if element.is_displayed()
                ]

                if visible_elements:
                    substantial_shareholders_tab = (
                        visible_elements[0]
                    )
                    break

                time.sleep(0.2)

            if substantial_shareholders_tab is None:
                return {
                    "substantial_shareholders": [],
                    "shareholders_subject_to_lock_up": [],
                }

            driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    block: 'center',
                    inline: 'center'
                });
                """,
                substantial_shareholders_tab,
            )

            driver.get_log("performance")

            driver.execute_script(
                "arguments[0].click();",
                substantial_shareholders_tab,
            )

            deadline = time.time() + 15

            while time.time() < deadline:
                logs = driver.get_log(
                    "performance"
                )

                for entry in logs:
                    message = json.loads(
                        entry["message"]
                    )["message"]

                    if (
                        message["method"]
                        != "Network.responseReceived"
                    ):
                        continue

                    response = message[
                        "params"
                    ]["response"]

                    response_url = response["url"]

                    if (
                        "NJhistoryOfMajorShareHolder"
                        not in response_url
                        or f"symbol={symbol}"
                        not in response_url
                        or "history=0"
                        not in response_url
                    ):
                        continue

                    request_id = message[
                        "params"
                    ]["requestId"]

                    try:
                        result = (
                            driver.execute_cdp_cmd(
                                "Network.getResponseBody",
                                {
                                    "requestId": request_id,
                                },
                            )
                        )

                        return (
                            self._parse_substantial_shareholders(
                                result["body"]
                            )
                        )

                    except Exception:
                        pass

                time.sleep(0.2)

        except Exception:
            pass

        return {
            "substantial_shareholders": [],
            "shareholders_subject_to_lock_up": [],
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

        def parse_table(
            table_id: str,
        ) -> list[dict]:
            table = soup.find(
                "table",
                id=table_id,
            )

            if table is None:
                return []

            rows = table.select(
                "tbody tr"
            )

            shareholders = []

            for row in rows:
                cells = row.find_all("td")

                if len(cells) < 5:
                    continue

                if (
                    len(cells) == 1
                    or "no-records-found"
                    in row.get(
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
                        "total_shares_held_trading_day":
                            values[2],
                        "total_shares_held_prev_trading_day":
                            values[3],
                        "total_shares_change":
                            values[4],
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

    def _open_financial_information(
        self,
        driver,
    ) -> None:
        deadline = time.time() + 15
        previous_periods = None

        while time.time() < deadline:
            elements = driver.find_elements(
                By.CLASS_NAME,
                "displayPrevBtn",
            )

            visible_elements = [
                element
                for element in elements
                if element.is_displayed()
            ]

            if visible_elements:
                previous_periods = (
                    visible_elements[0]
                )
                break

            time.sleep(0.2)

        if previous_periods is None:
            raise RuntimeError(
                "Display Previous Periods "
                "button was not found."
            )

        driver.execute_script(
            """
            arguments[0].scrollIntoView({
                block: 'center',
                inline: 'center'
            });
            """,
            previous_periods,
        )

        driver.execute_script(
            "arguments[0].click();",
            previous_periods,
        )

        time.sleep(1)

        deadline = time.time() + 15
        financial_information = None

        while time.time() < deadline:
            elements = driver.find_elements(
                By.ID,
                "balancesheet",
            )

            visible_elements = [
                element
                for element in elements
                if element.is_displayed()
            ]

            if visible_elements:
                financial_information = (
                    visible_elements[0]
                )
                break

            time.sleep(0.2)

        if financial_information is None:
            raise RuntimeError(
                "Financial Information tab "
                "was not found."
            )

        driver.execute_script(
            """
            arguments[0].scrollIntoView({
                block: 'center',
                inline: 'center'
            });
            """,
            financial_information,
        )

    def _get_financial_information(
        self,
        driver,
    ) -> dict:
        section = driver.find_element(
            By.ID,
            "unifiedSummaryFinancial",
        )

        tables = section.find_elements(
            By.TAG_NAME,
            "table",
        )

        if not tables:
            return {
                "balance_sheet": [],
                "statement_of_income": [],
                "cash_flows": [],
            }

        table = tables[0]

        rows = table.find_elements(
            By.TAG_NAME,
            "tr",
        )

        result = {
            "balance_sheet": [],
            "statement_of_income": [],
            "cash_flows": [],
        }

        current_statement = None
        periods = []

        statement_labels = {
            " ".join(
                self.labels["balance_sheet"].split()
            ).casefold(): "balance_sheet",

            " ".join(
                self.labels["statement_of_income"].split()
            ).casefold(): "statement_of_income",

            " ".join(
                self.labels["cash_flows"].split()
            ).casefold(): "cash_flows",
        }

        for row in rows:
            cells = row.find_elements(
                By.CSS_SELECTOR,
                "th, td",
            )

            values = [
                cell.text.strip()
                for cell in cells
            ]

            if not values:
                continue

            first_value = values[0]

            normalized_first_value = (
                " ".join(
                    first_value.split()
                ).casefold()
            )

            if normalized_first_value in statement_labels:
                current_statement = (
                    statement_labels[
                        normalized_first_value
                    ]
                )

                periods = [
                    value
                    for value in values[1:]
                    if value
                ]

                continue

            if first_value in {
                "All Figures in",
                "All Currency In",
                "Last Update Date",
                "جميع الأرقام بال",
                "العملة في",
                "تاريخ آخر تحديث",
            }:
                continue

            if current_statement is None:
                continue

            metric = first_value

            if not metric:
                continue

            for index, period in enumerate(
                periods,
                start=1,
            ):
                if index >= len(values):
                    break

                value = values[index].strip()

                parsed_value = (
                    self._parse_numeric_value(
                        value
                    )
                )

                result[
                    current_statement
                ].append(
                    {
                        "period": period,
                        "metric": metric,
                        "value": parsed_value,
                    }
                )

        return result

    def _get_statement(
        self,
        driver,
        symbol: str,
        statement_type: int,
    ) -> list[dict]:
        key = self.STATEMENT_TYPES[
            statement_type
        ]

        driver.get_log("performance")

        label = self.labels[key]

        elements = driver.find_elements(
            By.XPATH,
            "//*[self::a or self::li or self::button]"
            "[contains("
            "normalize-space(.), "
            f"'{label}'"
            ")]",
        )

        visible_elements = [
            element
            for element in elements
            if element.is_displayed()
        ]

        if not visible_elements:
            return []

        tab = visible_elements[0]

        driver.execute_script(
            """
            arguments[0].scrollIntoView({
                block: 'center',
                inline: 'center'
            });
            """,
            tab,
        )

        driver.execute_script(
            "arguments[0].click();",
            tab,
        )

        deadline = time.time() + 20

        while time.time() < deadline:
            logs = driver.get_log(
                "performance"
            )

            for entry in logs:
                try:
                    message = json.loads(
                        entry["message"]
                    )["message"]

                except Exception:
                    continue

                if (
                    message["method"]
                    != "Network.responseReceived"
                ):
                    continue

                response = message[
                    "params"
                ]["response"]

                response_url = response.get(
                    "url",
                    "",
                )

                if (
                    "NJstatementsTabData"
                    not in response_url
                    or (
                        f"statementType={statement_type}"
                        not in response_url
                    )
                    or "reportType=0"
                    not in response_url
                    or (
                        f"requestLocale={self.language}"
                        not in response_url
                    )
                    or f"symbol={symbol}"
                    not in response_url
                ):
                    continue

                if response.get("status") != 200:
                    continue

                request_id = message[
                    "params"
                ]["requestId"]

                try:
                    result = (
                        driver.execute_cdp_cmd(
                            "Network.getResponseBody",
                            {
                                "requestId": request_id,
                            },
                        )
                    )

                    body = result.get(
                        "body",
                        "",
                    )

                    if not body:
                        continue

                    return (
                        self._parse_statement(
                            body
                        )
                    )

                except Exception:
                    continue

            time.sleep(0.2)

        return []

    @staticmethod
    def _parse_statement(
        html: str,
    ) -> list[dict]:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        tables = soup.find_all("table")

        if not tables:
            return []

        table = tables[0]

        rows = table.find_all("tr")

        if not rows:
            return []

        periods = []

        for row in rows:
            headers = row.find_all("th")

            if not headers:
                continue

            for header in headers[1:]:
                text = header.get_text(
                    " ",
                    strip=True,
                )

                if text:
                    periods.append(text)

            if periods:
                break

        if not periods:
            return []

        records = []

        for row in rows:
            cells = row.find_all("td")

            if len(cells) < 2:
                continue

            metric = cells[0].get_text(
                " ",
                strip=True,
            )

            if not metric:
                continue

            if metric in {
                "All Figures in",
                "All Currency In",
                "Last Update Date",
                "جميع الأرقام بال",
                "العملة في",
                "تاريخ آخر تحديث",
            }:
                continue

            values = []

            for cell in cells[1:]:
                value = cell.get_text(
                    " ",
                    strip=True,
                )

                values.append(
                    CompanyScraper
                    ._parse_numeric_value(
                        value
                    )
                )

            for index, value in enumerate(
                values
            ):
                if index >= len(periods):
                    break

                records.append(
                    {
                        "period": periods[index],
                        "metric": metric,
                        "value": value,
                    }
                )

        return records

    @staticmethod
    def _parse_numeric_value(
        value: str,
    ):
        if not value or value == "-":
            return None

        value_without_commas = (
            value.replace(",", "")
        )

        try:
            return int(
                value_without_commas
            )

        except ValueError:
            try:
                return float(
                    value_without_commas
                )

            except ValueError:
                return value

    @staticmethod
    def _get_file_type(
        url: str,
    ) -> str:
        url_lower = url.lower()

        if url_lower.endswith(".pdf"):
            return "pdf"

        if url_lower.endswith(".xls"):
            return "xls"

        if url_lower.endswith(".xlsx"):
            return "xlsx"

        if url_lower.endswith(".html"):
            return "html"

        return "unknown"