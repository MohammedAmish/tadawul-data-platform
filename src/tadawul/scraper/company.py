from __future__ import annotations

import json
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from tadawul.scraper.browser import TadawulBrowser


class CompanyScraper:
    STATEMENT_TYPES = {
        0: "balance_sheet",
        1: "statement_of_income",
        2: "cash_flows",
    }

    def __init__(self, headless: bool = False):
        self.headless = headless

    def scrape(self, company: dict) -> dict:
        symbol = company["company"]

        url = urljoin(
            TadawulBrowser.BASE_URL,
            company["link"],
        )

        result = {
            "symbol": symbol,
            "company_name": company["companyDisplay"],
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
            "foreign_ownership": None,
            "substantial_shareholders": {
                "substantial_shareholders": [],
                "shareholders_subject_to_lock_up": [],
            },
            "balance_sheet": [],
            "statement_of_income": [],
            "cash_flows": [],
        }

        with TadawulBrowser(headless=self.headless) as driver:
            driver.get(url)

            # ------------------------------------------------------------------
            # Company information
            # ------------------------------------------------------------------

            market, sector = self._get_market_and_sector(driver)

            result["market"] = market
            result["sector"] = sector

            result["shares_type"] = self._get_exact_text(
                driver,
                "Common Shares",
            )

            result["company_profile"] = self._get_company_profile(
                driver
            )
            
            result["subsidiaries"] = self._get_subsidiaries(driver)

            result["company_details"] = self._get_company_details(
                driver
            )

            result["management_team"] = self._get_management_team(
                driver
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

            # ------------------------------------------------------------------
            # Financial information
            # ------------------------------------------------------------------

            self._open_financial_information(driver)

            for statement_type, key in self.STATEMENT_TYPES.items():
                records = self._get_statement(
                    driver,
                    symbol,
                    statement_type,
                )

                result[key] = records

        return result

    # ==========================================================================
    # COMPANY SCRAPER
    # ==========================================================================

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

    @staticmethod
    def _get_market_and_sector(
        driver,
    ) -> tuple[str | None, str | None]:
        market = driver.find_element(
            By.XPATH,
            "//li[normalize-space()='Main Market']",
        )

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

    @staticmethod
    def _get_company_profile(driver) -> dict:
        container = driver.find_element(
            By.CSS_SELECTOR,
            "div.fundInfo",
        )

        paragraphs = container.find_elements(
            By.TAG_NAME,
            "p",
        )

        profile = {}

        for paragraph in paragraphs:
            text = paragraph.text.strip()

            if text == "Company overview":
                profile["company_overview"] = (
                    paragraph.find_element(
                        By.XPATH,
                        "following-sibling::p[1]",
                    ).text.strip()
                )

            elif text == "Company History":
                profile["company_history"] = (
                    paragraph.find_element(
                        By.XPATH,
                        "following-sibling::p[1]",
                    ).text.strip()
                )

            elif text == "Company Bylaws":
                link = paragraph.find_element(
                    By.XPATH,
                    "following-sibling::p[1]//a",
                )

                profile["company_bylaws_url"] = (
                    link.get_attribute("href")
                )

        equity = container.find_element(
            By.XPATH,
            ".//p[strong[normalize-space()='Equity Profile']]"
            "/following-sibling::div[contains(@class, 'inspectionBox')][1]",
        )

        for item in equity.find_elements(
            By.CSS_SELECTOR,
            "li",
        ):
            spans = item.find_elements(
                By.TAG_NAME,
                "span",
            )

            strongs = item.find_elements(
                By.TAG_NAME,
                "strong",
            )

            if spans and strongs:
                key = spans[0].text.strip()
                value = strongs[0].text.strip()

                if key:
                    profile[key] = value

        return profile
    
    @staticmethod
    def _get_subsidiaries(driver) -> list[dict]:
        """
        Extract subsidiaries from the Company Profile page.

        Not every company has subsidiaries. If the subsidiary
        table does not exist, return an empty list.
        """

        tables = driver.find_elements(
            By.XPATH,
            "//table[.//th[contains("
            "translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
            "'abcdefghijklmnopqrstuvwxyz'), "
            "'name of subsidiary'"
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
                    ownership.replace("%", "").strip()
                )
            except ValueError:
                ownership_percentage = None

            subsidiaries.append(
                {
                    "name": name,
                    "ownership_percentage": ownership_percentage,
                    "main_business": values[2] or None,
                    "location": values[3] or None,
                    "country": values[4] or None,
                }
            )

        return subsidiaries

    @staticmethod
    def _get_company_details(driver) -> dict:
        container = driver.find_element(
            By.CSS_SELECTOR,
            "div.companyProfile",
        )

        text = container.text.strip()

        details = {
            "date_established": None,
            "financial_year_end": None,
            "listing_date": None,
            "external_auditors": None,
            "isin_code": None,
            "number_of_employees": None,
            "investor_relations": {},
        }

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        fields = {
            "Date Established": "date_established",
            "Financial Year End": "financial_year_end",
            "Listing Date": "listing_date",
            "External Auditors": "external_auditors",
            "ISIN CODE": "isin_code",
            "Number of Employees": "number_of_employees",
        }

        for index, line in enumerate(lines):
            if line in fields and index + 1 < len(lines):
                details[fields[line]] = lines[index + 1]

        investor_relations = details["investor_relations"]

        for index, line in enumerate(lines):
            if (
                line == "Contact Name:"
                and index + 1 < len(lines)
            ):
                investor_relations["contact_name"] = (
                    lines[index + 1]
                )

            elif (
                line == "Company Address:"
                and index + 1 < len(lines)
            ):
                investor_relations["company_address"] = (
                    lines[index + 1]
                )

            elif line == "Contact Details:":
                contact_details = []

                for value in lines[index + 1:]:
                    if value in {
                        "Company Website:",
                        "Add To Watchlist",
                    }:
                        break

                    contact_details.append(value)

                investor_relations["contact_details"] = (
                    contact_details
                )

            elif (
                line == "Company Website:"
                and index + 1 < len(lines)
            ):
                investor_relations["company_website"] = (
                    lines[index + 1]
                )

        return details

    @staticmethod
    def _get_management_team(driver) -> dict:
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
                "./p[strong[contains(@class, 'namePopup')]]",
            )

            for person in people:
                name_element = person.find_element(
                    By.CSS_SELECTOR,
                    "strong.namePopup",
                )

                name = (
                    name_element
                    .get_attribute("textContent")
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
                    .get_attribute("textContent")
                    .strip()
                )

                if person_text.startswith(name):
                    role = person_text[len(name):].strip()

                    if role:
                        person_data["role"] = role

                popup_id = name_element.get_attribute("id")

                if popup_id:
                    popup_id = popup_id.replace(
                        "namePopup_",
                        "namePopupBox_",
                    )

                    popups = group.find_elements(
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
                                .get_attribute("textContent")
                                .strip()
                            )

                            value = (
                                fields[index + 1]
                                .get_attribute("textContent")
                                .strip()
                            )

                            if key == "BD Session Start":
                                person_data[
                                    "bd_session_start"
                                ] = value

                            elif key == "BD Session End":
                                person_data[
                                    "bd_session_end"
                                ] = value

                            elif key == "Designation":
                                person_data[
                                    "designation"
                                ] = value

                            elif key == "Classification":
                                person_data[
                                    "classification"
                                ] = value

                if heading == "Senior Executives":
                    senior_executives.append(person_data)
                else:
                    board_of_directors.append(person_data)

        return {
            "board_of_directors": board_of_directors,
            "senior_executives": senior_executives,
        }

    @staticmethod
    def _get_financial_statements_and_reports(
        driver,
        symbol: str,
    ) -> list[dict]:
        driver.get_log("performance")

        tab = driver.find_element(
            By.ID,
            "finacialStatementAndReports",
        )

        driver.execute_script(
            "arguments[0].click();",
            tab,
        )

        deadline = time.time() + 15

        while time.time() < deadline:
            logs = driver.get_log("performance")

            for entry in logs:
                message = json.loads(
                    entry["message"]
                )["message"]

                if message["method"] != "Network.responseReceived":
                    continue

                response = message["params"]["response"]
                response_url = response["url"]

                if (
                    "NJstatementsTabData" not in response_url
                    or "statementType=6" not in response_url
                    or "reportType=0" not in response_url
                    or "requestLocale=en" not in response_url
                    or f"symbol={symbol}" not in response_url
                ):
                    continue

                request_id = message["params"]["requestId"]

                try:
                    result = driver.execute_cdp_cmd(
                        "Network.getResponseBody",
                        {
                            "requestId": request_id,
                        },
                    )

                    return CompanyScraper._parse_financial_reports(
                        result["body"]
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
                current_section = section_header.get_text(
                    " ",
                    strip=True,
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
                            detected_years.append(year)

            if len(detected_years) >= 2:
                current_years = detected_years
                continue

            if not current_section or not current_years:
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

            for index, cell in enumerate(cells[1:]):
                if index >= len(current_years):
                    break

                year = current_years[index]

                publication_date = None

                date_element = cell.find("p")

                if date_element:
                    publication_date = date_element.get_text(
                        " ",
                        strip=True,
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
                            "section": current_section,
                            "period": period,
                            "year": year,
                            "publication_date": publication_date,
                            "file_type": CompanyScraper._get_file_type(
                                href
                            ),
                            "file_url": urljoin(
                                TadawulBrowser.BASE_URL,
                                href,
                            ),
                        }
                    )

        return reports

    @staticmethod
    def _get_foreign_ownership(
        driver,
        symbol: str,
    ) -> dict | None:
        # Clear old performance logs
        driver.get_log("performance")

        try:
            # Find ALL matching elements and choose the visible tab.
            deadline = time.time() + 15
            foreign_ownership_tab = None

            while time.time() < deadline:
                elements = driver.find_elements(
                    By.XPATH,
                    "//li[normalize-space()='Foreign Ownership']",
                )

                visible_elements = [
                    element
                    for element in elements
                    if element.is_displayed()
                ]

                if visible_elements:
                    foreign_ownership_tab = visible_elements[0]
                    break

                time.sleep(0.2)

            if foreign_ownership_tab is None:
                return None

            # Make sure the tab is in view.
            driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    block: 'center',
                    inline: 'center'
                });
                """,
                foreign_ownership_tab,
            )

            # Clear logs immediately before clicking.
            driver.get_log("performance")

            driver.execute_script(
                "arguments[0].click();",
                foreign_ownership_tab,
            )

            # Wait for the actual XHR response generated by the tab.
            deadline = time.time() + 15

            while time.time() < deadline:
                logs = driver.get_log("performance")

                for entry in logs:
                    message = json.loads(
                        entry["message"]
                    )["message"]

                    if message["method"] != "Network.responseReceived":
                        continue

                    response = message["params"]["response"]
                    response_url = response["url"]

                    if (
                        "NJforeginOwnerShip" not in response_url
                        or f"symbol={symbol}" not in response_url
                    ):
                        continue

                    request_id = message["params"]["requestId"]

                    try:
                        result = driver.execute_cdp_cmd(
                            "Network.getResponseBody",
                            {
                                "requestId": request_id,
                            },
                        )

                        body = result["body"]

                        return CompanyScraper._parse_foreign_ownership(
                            body
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
            "foreign_strategic_investors_ownership_percent": None,
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

        # Total Foreign Ownership
        if sections:
            values = sections[0].find_all(
                "strong"
            )

            if len(values) >= 2:
                maximum_limit = values[0].get_text(
                    " ",
                    strip=True,
                )

                actual = values[1].get_text(
                    " ",
                    strip=True,
                )

                try:
                    result["total_foreign_ownership"][
                        "maximum_limit_percent"
                    ] = float(maximum_limit)
                except ValueError:
                    pass

                try:
                    result["total_foreign_ownership"][
                        "actual_percent"
                    ] = float(actual)
                except ValueError:
                    pass

        # Foreign Strategic Investors Ownership
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

        # Last updated date
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
                    text.split(":", 1)[1].strip()
                )

        return result

    @staticmethod
    def _get_substantial_shareholders(
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
                    "//li[normalize-space()='Substantial Shareholders']",
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
                logs = driver.get_log("performance")

                for entry in logs:
                    message = json.loads(
                        entry["message"]
                    )["message"]

                    if message["method"] != "Network.responseReceived":
                        continue

                    response = message["params"]["response"]
                    response_url = response["url"]

                    if (
                        "NJhistoryOfMajorShareHolder"
                        not in response_url
                        or f"symbol={symbol}" not in response_url
                        or "history=0" not in response_url
                    ):
                        continue

                    request_id = message["params"]["requestId"]

                    try:
                        result = driver.execute_cdp_cmd(
                            "Network.getResponseBody",
                            {
                                "requestId": request_id,
                            },
                        )

                        return CompanyScraper._parse_substantial_shareholders(
                            result["body"]
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

        def parse_table(table_id: str) -> list[dict]:
            table = soup.find(
                "table",
                id=table_id,
            )

            if table is None:
                return []

            rows = table.select("tbody tr")

            shareholders = []

            for row in rows:
                cells = row.find_all("td")

                if len(cells) < 5:
                    continue

                if (
                    len(cells) == 1
                    or "no-records-found" in row.get(
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
                        "total_shares_held_trading_day": (
                            values[2]
                        ),
                        "total_shares_held_prev_trading_day": (
                            values[3]
                        ),
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

    # ==========================================================================
    # FINANCIALS SCRAPER
    # ==========================================================================

    @staticmethod
    def _open_financial_information(driver) -> None:
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
                previous_periods = visible_elements[0]
                break

            time.sleep(0.2)

        if previous_periods is None:
            raise RuntimeError(
                "Display Previous Periods button was not found."
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
                financial_information = visible_elements[0]
                break

            time.sleep(0.2)

        if financial_information is None:
            raise RuntimeError(
                "Financial Information tab was not found."
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

    @staticmethod
    def _get_statement(
        driver,
        symbol: str,
        statement_type: int,
    ) -> list[dict]:
        key = CompanyScraper.STATEMENT_TYPES[
            statement_type
        ]

        # Clear old performance logs before triggering
        # the statement request.
        driver.get_log("performance")

        if statement_type == 0:
            # Balance Sheet is the Financial Information tab.
            elements = driver.find_elements(
                By.ID,
                "balancesheet",
            )
        else:
            # Statement of Income and Cash Flows are
            # controls inside the Financial Information tab.
            elements = driver.find_elements(
                By.XPATH,
                "//*[self::a or self::li or self::button]"
                "[contains("
                "translate(normalize-space(.), "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                "'abcdefghijklmnopqrstuvwxyz'), "
                f"'{key.replace('_', ' ')}'"
                ")]",
            )

        visible_elements = [
            element
            for element in elements
            if element.is_displayed()
        ]

        if not visible_elements:
            # Tadawul's visible text does not always map cleanly
            # to the normalized key above, so use the known
            # statement labels as a fallback.
            labels = {
                0: "Balance Sheet",
                1: "Statement of Income",
                2: "Cash Flows",
            }

            label = labels[statement_type]

            elements = driver.find_elements(
                By.XPATH,
                "//*[self::a or self::li or self::button]"
                f"[contains(normalize-space(.), '{label}')]",
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
            logs = driver.get_log("performance")

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

                response = message["params"]["response"]
                response_url = response.get("url", "")

                if (
                    "NJstatementsTabData" not in response_url
                    or f"statementType={statement_type}"
                    not in response_url
                    or "reportType=0" not in response_url
                    or "requestLocale=en" not in response_url
                    or f"symbol={symbol}" not in response_url
                ):
                    continue

                if response.get("status") != 200:
                    continue

                request_id = message["params"]["requestId"]

                try:
                    result = driver.execute_cdp_cmd(
                        "Network.getResponseBody",
                        {"requestId": request_id},
                    )

                    body = result.get("body", "")

                    if not body:
                        continue

                    return CompanyScraper._parse_statement(
                        body
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
            }:
                continue

            values = []

            for cell in cells[1:]:
                value = cell.get_text(
                    " ",
                    strip=True,
                )

                if value == "-":
                    value = None

                elif value:
                    value = value.replace(",", "")

                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass

                values.append(value)

            for index, value in enumerate(values):
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
    def _get_file_type(url: str) -> str:
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