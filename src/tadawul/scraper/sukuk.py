from __future__ import annotations

import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from tadawul.scraper.browser import TadawulBrowser


class SukukScraper:
    """
    Scraper for Tadawul Corporate Sukuk/Bonds profiles.
    """

    STATEMENT_TYPES = {
        6: "financial_information",
        7: "financial_statements_and_reports",
        0: "balance_sheet",
        1: "statement_of_income",
        2: "cash_flows",
    }

    ISSUANCE_LABELS = {
        # English
        "Issuer": "issuer",
        "Listing Date": "listing_date",
        "Lead Manager": "issuer_manager",
        "Issuance Credit Rating": "issue_credit_rating",
        "Issuer Credit Rating": "issuer_credit_rating",
        "Debt Instrument Status": "legal_status",
        "Debt Instrument Type and Structure": (
            "debt_instrument_type"
        ),
        "Accumulative Issuance Amount ( ^ )": "total_issue_amount",
        "Issue Date": "issue_date",
        "Maturity and Early Redemption Date": (
            "maturity_date_and_early_redemption"
        ),
        "Coupon Rate %": "profit_margin",
        "Coupon Distribution Frequency": (
            "profit_distribution_frequency"
        ),
        "Zakat treatment": "zakat_treatment",
        "Trading Method": "trading_method",
        "Collateral": "guarantees",
        "Minimum Subscription Amount Per Investor": "minimum_subscription",
        "Par Value": "par_value",
        "Identification Code": "isin",
        "Registrar": "registrar",
        "Payment Administrator": "payment_agent",
        "Debt Instrument Agent": (
            "debt_instrument_holders_agent"
        ),

        # Arabic
        "المصدر": "issuer",
        "تاريخ الإدراج": "listing_date",
        "مدير المصدر": "issuer_manager",
        "التصنيف الائتماني للإصدار": (
            "issue_credit_rating"
        ),
        "التصنيف الائتماني للمصدر": (
            "issuer_credit_rating"
        ),
        "الوضع النظامي لأداة الدين": "legal_status",
        "نوع وهيكلة أداة الدين": (
            "debt_instrument_type"
        ),
        "القيمة الاجمالية لإصدار ( ^ )": (
            "total_issue_amount"
        ),
        "تاريخ الإصدار": "issue_date",
        "تاريخ الانتهاء والاسترداد المبكر": (
            "maturity_date_and_early_redemption"
        ),
        "هامش الربحية": "profit_margin",
        "مدة توزيع الربحية": (
            "profit_distribution_frequency"
        ),
        "المعاملة الزكوية": "zakat_treatment",
        "طريقة التداول": "trading_method",
        "الضمانات": "guarantees",
        "الحد الأدنى للاكتتاب": "minimum_subscription",
        "القيمة الاسمية": "par_value",
        "رمز التعريف": "isin",
        "المسجل": "registrar",
        "مدير الدفعات": "payment_agent",
        "وكيل حملة أدوات الدين": (
            "debt_instrument_holders_agent"
        ),
    }

    EQUITY_LABELS = {
        # English
        "Authorized Capital ( ^ )": "authorized_capital",
        "Issued Shares": "issued_shares",
        "Paid Capital ( ^ )": "paid_capital",
        "Per Value/Share": "basic_share_value",
        "Paid up Value/Share": "paid_value_per_share",
        "Last Update": "last_update",

        # Arabic
        "رأس المال المصرح به ( ^ )": (
            "authorized_capital"
        ),
        "عدد الأسهم المصدرة": "issued_shares",
        "رأس المال المدفوع ( ^ )": (
            "paid_capital"
        ),
        "القيمة الأساسية للسهم": (
            "basic_share_value"
        ),
        "القيمة المدفوعة للسهم": (
            "paid_value_per_share"
        ),
        "اخر تحديث": "last_update",
    }

    BASIC_INFORMATION_LABELS = {
        # English
        "Date Established": "establishment_date",
        "Financial Year End": "fiscal_year_end",
        "Listing Date": "listing_date",
        "External Auditors": "auditors",
        "Number Of Employees": "number_of_employees",

        # Arabic
        "تاريخ التأسيس": "establishment_date",
        "نهاية السنة المالية": "fiscal_year_end",
        "تاريخ الإدراج": "listing_date",
        "مراجعيي الحسابات": "auditors",
        "عدد الموظفين": "number_of_employees",
    }

    COUPON_LABELS = {
        # English
        "From": "from",
        "To": "to",
        "Number Of Days To Coupon": "days_to_coupon",
        "Coupon Rate": "coupon_rate",
        "Payment Per Sukuk/Bond ( ^ )": (
            "payment_per_sukuk_bond"
        ),

        # Arabic
        "من": "from",
        "إلى": "to",
        "عدد الأيام إلى القسيمة": (
            "days_to_coupon"
        ),
        "(%) نسبة العائد": "coupon_rate",
        "قيمة العائد ( ^ )": (
            "payment_per_sukuk_bond"
        ),
    }

    def __init__(
        self,
        browser: TadawulBrowser,
        language: str = "en",
    ):
        self.browser = browser
        self.language = language

    # ------------------------------------------------------------------
    # Main scraper
    # ------------------------------------------------------------------

    def scrape(self, record: dict) -> dict:
        """
        Scrape one Sukuk/Bond profile.

        Parameters
        ----------
        record:
            Record returned by NJgetSukukMarketDetails.
        """

        symbol = record.get("symbol")

        if not symbol:
            raise ValueError(
                "Sukuk/Bond record does not contain a symbol"
            )

        profile_url = record.get("cUrl")

        if not profile_url:
            raise ValueError(
                f"Sukuk/Bond {symbol} does not contain cUrl"
            )

        profile_url = self._build_profile_url(
            profile_url
        )

        self.browser.open(
            profile_url,
            wait_seconds=10,
        )

        html = self.browser.driver.page_source

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        result = {
            "symbol": symbol,
            "issuer_name": record.get("issuerName"),
            "sector_name": record.get("sectorName"),
            "coupon_payments": [],
            "issuance_profile": {},
            "issuer_profile": {},
            "financial_statements_and_reports": [],
            "financial_information": {
                "balance_sheet": [],
                "statement_of_income": [],
                "cash_flows": [],
            },
            "balance_sheet": [],
            "statement_of_income": [],
            "cash_flows": [],
        }

        # --------------------------------------------------------------
        # Static profile information
        # --------------------------------------------------------------

        result["issuance_profile"] = (
            self._parse_issuance_profile(
                soup
            )
        )

        result["issuer_profile"] = (
            self._parse_issuer_profile(
                soup
            )
        )

        result["coupon_payments"] = (
            self._parse_coupon_payments(
                soup
            )
        )

        # --------------------------------------------------------------
        # Dynamic financial information
        # --------------------------------------------------------------

        result["financial_information"] = (
            self._get_statement(
                statement_type=6,
                symbol=symbol,
            )
        )

        result["financial_statements_and_reports"] = (
            self._get_statement(
                statement_type=7,
                symbol=symbol,
            )
        )

        # --------------------------------------------------------------
        # Previous periods
        # --------------------------------------------------------------

        self._open_previous_periods()

        result["balance_sheet"] = (
            self._get_statement(
                statement_type=0,
                symbol=symbol,
            )
        )

        result["statement_of_income"] = (
            self._get_statement(
                statement_type=1,
                symbol=symbol,
            )
        )

        result["cash_flows"] = (
            self._get_statement(
                statement_type=2,
                symbol=symbol,
            )
        )

        return result

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    def _build_profile_url(
        self,
        profile_url: str,
    ) -> str:
        """
        Use Tadawul's dynamically supplied cUrl exactly as returned.
        """

        if profile_url.startswith("http"):
            return profile_url

        return (
            self.browser.BASE_URL
            + profile_url
        )

    # ------------------------------------------------------------------
    # Issuance Profile
    # ------------------------------------------------------------------

    def _parse_issuance_profile(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        result = {}

        tables = soup.select(
            ".fundInfoTable"
        )

        for container in tables:
            heading = container.find("h3")

            if heading is None:
                continue

            title = self._clean_text(
                heading.get_text(
                    " ",
                    strip=True,
                )
            )

            if title not in {
                "Issuance Profile",
                "ملف الإصدار",
            }:
                continue

            table = container.find("table")

            if table is None:
                return result

            for row in table.select(
                "tbody tr"
            ):
                cells = row.find_all("td")

                if len(cells) < 2:
                    continue

                key = self._clean_text(
                    cells[0].get_text(
                        " ",
                        strip=True,
                    )
                )

                value = self._clean_text(
                    cells[1].get_text(
                        " ",
                        strip=True,
                    )
                )

                if not key:
                    continue

                standardized_key = (
                    self.ISSUANCE_LABELS.get(
                        key,
                        key,
                    )
                )

                result[
                    standardized_key
                ] = value

            break

        return result

    # ------------------------------------------------------------------
    # Issuer Profile
    # ------------------------------------------------------------------

    def _parse_issuer_profile(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        result = {
            "issuer_overview": None,
            "issuer_history": None,
            "equity_profile": {},
            "basic_information": {},
            "management_team": [],
            "investor_relations": {},
        }

        company_profile = soup.select_one(
            ".companyProfile"
        )

        if company_profile:
            headings = company_profile.find_all(
                "h3"
            )

            for heading in headings:
                title = self._clean_text(
                    heading.get_text(
                        " ",
                        strip=True,
                    )
                )

                paragraph = heading.find_next_sibling(
                    "p"
                )

                if paragraph is None:
                    continue

                text = self._clean_text(
                    paragraph.get_text(
                        " ",
                        strip=True,
                    )
                )

                if title in {
                    "Issuer Overview",
                    "نبذة عن نشاط المُصدر",
                }:
                    result["issuer_overview"] = text

                elif title in {
                    "Issuer History",
                    "نبذة عن تاريخ المُصدر",
                }:
                    result["issuer_history"] = text

        result["equity_profile"] = (
            self._parse_equity_profile(
                soup
            )
        )

        result["basic_information"] = (
            self._parse_basic_information(
                soup
            )
        )

        result["management_team"] = (
            self._parse_management_team(
                soup
            )
        )

        result["investor_relations"] = (
            self._parse_investor_relations(
                soup
            )
        )

        return result

    # ------------------------------------------------------------------
    # Equity Profile
    # ------------------------------------------------------------------

    def _parse_equity_profile(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        result = {}

        for table in soup.find_all("table"):
            heading = table.find("thead")

            if heading is None:
                continue

            heading_text = self._clean_text(
                heading.get_text(
                    " ",
                    strip=True,
                )
            )

            if heading_text not in {
                "Equity Profile",
                "ملف الأسهم",
            }:
                continue

            for cell in table.select(
                "tbody td"
            ):
                strong = cell.find("strong")

                if strong is None:
                    continue

                value = self._clean_text(
                    strong.get_text(
                        " ",
                        strip=True,
                    )
                )

                cell_text = self._clean_text(
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                )

                label = cell_text

                if value:
                    label = label.replace(
                        value,
                        "",
                        1,
                    ).strip()

                label = self._clean_text(
                    label
                )

                if not label:
                    continue

                standardized_key = (
                    self.EQUITY_LABELS.get(
                        label,
                        label,
                    )
                )

                result[
                    standardized_key
                ] = value

            break

        return result

    # ------------------------------------------------------------------
    # Basic Information
    # ------------------------------------------------------------------

    def _parse_basic_information(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        result = {}

        sections = soup.select(
            ".company_management_tab_dtl"
        )

        if not sections:
            return result

        container = sections[0]

        for item in container.select("li"):
            heading = item.find("h4")
            paragraph = item.find("p")

            if heading is None or paragraph is None:
                continue

            key = self._clean_text(
                heading.get_text(
                    " ",
                    strip=True,
                )
            )

            value = self._clean_text(
                paragraph.get_text(
                    " ",
                    strip=True,
                )
            )

            if not key:
                continue

            standardized_key = (
                self.BASIC_INFORMATION_LABELS.get(
                    key,
                    key,
                )
            )

            result[
                standardized_key
            ] = value

        return result

    # ------------------------------------------------------------------
    # Management Team
    # ------------------------------------------------------------------

    def _parse_management_team(
        self,
        section: BeautifulSoup,
    ) -> list[dict]:
        result = []

        management_sections = section.select(
            ".company_management_tab_dtl"
        )

        if len(management_sections) < 2:
            return result

        container = management_sections[1]

        current_group = None

        for element in container.find_all(
            ["h4", "p"]
        ):
            if element.name == "h4":
                current_group = self._clean_text(
                    element.get_text(
                        " ",
                        strip=True,
                    )
                )
                continue

            name_element = element.find(
                "strong",
                class_="namePopup",
            )

            if name_element is None:
                continue

            name = self._clean_text(
                name_element.get_text(
                    " ",
                    strip=True,
                )
            )

            popup_id = name_element.get("id")

            person = {
                "name": name,
                "group": current_group,
                "designation": None,
                "classification": None,
                "bd_session_start": None,
                "bd_session_end": None,
            }

            if popup_id:
                popup = section.find(
                    id=popup_id.replace(
                        "namePopup_",
                        "namePopupBox_",
                    )
                )

                if popup:
                    labels = popup.select(
                        ".topTxt"
                    )

                    values = popup.select(
                        ".btmTxt"
                    )

                    popup_data = {}

                    for label, value in zip(
                        labels,
                        values,
                    ):
                        key = self._clean_text(
                            label.get_text(
                                " ",
                                strip=True,
                            )
                        )

                        popup_data[key] = (
                            self._clean_text(
                                value.get_text(
                                    " ",
                                    strip=True,
                                )
                            )
                        )

                    person[
                        "bd_session_start"
                    ] = (
                        popup_data.get(
                            "BD Session Start"
                        )
                        or popup_data.get(
                            "تاريخ بداية دورة المجلس"
                        )
                    )

                    person[
                        "bd_session_end"
                    ] = (
                        popup_data.get(
                            "BD Session End"
                        )
                        or popup_data.get(
                            "تاريخ نهاية دورة المجلس"
                        )
                    )

                    person[
                        "designation"
                    ] = (
                        popup_data.get(
                            "Designation"
                        )
                        or popup_data.get(
                            "منصب"
                        )
                    )

                    person[
                        "classification"
                    ] = (
                        popup_data.get(
                            "Classification"
                        )
                        or popup_data.get(
                            "صفة عضوية"
                        )
                    )

            result.append(person)

        return result

    # ------------------------------------------------------------------
    # Investor Relations
    # ------------------------------------------------------------------

    def _parse_investor_relations(
        self,
        section: BeautifulSoup,
    ) -> dict:
        result = {
            "contact_name": None,
            "address": None,
            "telephone": None,
            "fax": None,
            "email": None,
            "website": None,
        }

        investor_relations = section.select_one(
            ".investor_relations"
        )

        if investor_relations is None:
            return result

        headings = investor_relations.find_all(
            "h4"
        )

        for heading in headings:
            label = self._clean_text(
                heading.get_text(
                    " ",
                    strip=True,
                )
            )

            label = re.sub(
                r"\s*:\s*$",
                "",
                label,
            )

            paragraphs = []

            sibling = heading.find_next_sibling()

            while sibling:
                if sibling.name == "h4":
                    break

                if sibling.name == "p":
                    text = self._clean_text(
                        sibling.get_text(
                            " ",
                            strip=True,
                        )
                    )

                    if text:
                        paragraphs.append(text)

                sibling = sibling.find_next_sibling()

            if label in {
                "Contact Name",
                "اسم ضابط الاتصال",
            }:
                result["contact_name"] = (
                    paragraphs[0]
                    if paragraphs
                    else None
                )

            elif label in {
                "Address",
                "العنوان",
            }:
                result["address"] = (
                    " ".join(paragraphs)
                    if paragraphs
                    else None
                )

            elif label in {
                "Contact Details",
                "بيانات الإتصال",
            }:
                self._parse_contact_details(
                    investor_relations,
                    result,
                )

            elif label in {
                "Website",
                "الموقع الإلكتروني",
            }:
                if paragraphs:
                    result["website"] = (
                        paragraphs[0]
                    )

                link = heading.find_next_sibling(
                    "p"
                )

                if link:
                    anchor = link.find(
                        "a",
                        href=True,
                    )

                    if anchor:
                        result["website"] = (
                            anchor.get("href")
                        )

        email_link = investor_relations.select_one(
            'a[href^="mailto:"]'
        )

        if email_link:
            href = email_link.get(
                "href",
                "",
            )

            result["email"] = href.replace(
                "mailto:",
                "",
                1,
            ).strip()

        return result

    def _parse_contact_details(
        self,
        investor_relations: BeautifulSoup,
        result: dict,
    ) -> None:
        heading = None

        for candidate in investor_relations.find_all(
            "h4"
        ):
            label = self._clean_text(
                candidate.get_text(
                    " ",
                    strip=True,
                )
            )

            label = re.sub(
                r"\s*:\s*$",
                "",
                label,
            )

            if label in {
                "Contact Details",
                "بيانات الإتصال",
            }:
                heading = candidate
                break

        if heading is None:
            return

        paragraph = heading.find_next_sibling(
            "p"
        )

        if paragraph is None:
            return

        lines = []

        for part in paragraph.stripped_strings:
            text = self._clean_text(part)

            if text:
                lines.append(text)

        text = " ".join(lines)

        telephone_match = re.search(
            r"Telephone\s*:\s*(.*?)\s+FAX\s*:",
            text,
            re.IGNORECASE,
        )

        fax_match = re.search(
            r"FAX\s*:\s*(.*?)\s+Email\s*:",
            text,
            re.IGNORECASE,
        )

        email_match = re.search(
            r"Email\s*:\s*(.*)$",
            text,
            re.IGNORECASE,
        )

        if telephone_match:
            result["telephone"] = (
                telephone_match.group(1).strip()
            )

        if fax_match:
            result["fax"] = (
                fax_match.group(1).strip()
            )

        if email_match:
            result["email"] = (
                email_match.group(1).strip()
            )

        arabic_telephone_match = re.search(
            r"الهاتف\s*:\s*(.*?)\s+الفاكس\s*:",
            text,
        )

        arabic_fax_match = re.search(
            r"الفاكس\s*:\s*(.*?)\s+البريد الإلكتروني\s*:",
            text,
        )

        arabic_email_match = re.search(
            r"البريد الإلكتروني\s*:\s*(.*)$",
            text,
        )

        if arabic_telephone_match:
            result["telephone"] = (
                arabic_telephone_match.group(1).strip()
            )

        if arabic_fax_match:
            result["fax"] = (
                arabic_fax_match.group(1).strip()
            )

        if arabic_email_match:
            result["email"] = (
                arabic_email_match.group(1).strip()
            )

        email_link = paragraph.select_one(
            'a[href^="mailto:"]'
        )

        if email_link:
            result["email"] = (
                email_link.get(
                    "href",
                    "",
                )
                .replace(
                    "mailto:",
                    "",
                    1,
                )
                .strip()
            )

    # ------------------------------------------------------------------
    # Coupon Payments
    # ------------------------------------------------------------------

    def _parse_coupon_payments(
        self,
        soup: BeautifulSoup,
    ) -> list[dict]:
        result = []

        section = soup.select_one(
            ".couponPayment"
        )

        if section is None:
            return result

        table = section.find("table")

        if table is None:
            return result

        headers = []

        header_row = table.find("thead")

        if header_row:
            headers = [
                self._clean_text(
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                )
                for cell in header_row.find_all(
                    "th"
                )
            ]

        for row in table.select(
            "tbody tr"
        ):
            cells = row.find_all("td")

            if not cells:
                continue

            values = [
                self._clean_text(
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                )
                for cell in cells
            ]

            payment = {}

            for index, value in enumerate(
                values
            ):
                if index < len(headers):
                    key = headers[index]

                    standardized_key = (
                        self.COUPON_LABELS.get(
                            key,
                            key,
                        )
                    )

                    payment[
                        standardized_key
                    ] = value
                else:
                    payment[
                        f"column_{index + 1}"
                    ] = value

            result.append(payment)

        return result

    # ------------------------------------------------------------------
    # Dynamic financial statements
    # ------------------------------------------------------------------

    def _get_statement(
        self,
        statement_type: int,
        symbol: str,
    ):
        """
        Trigger and capture one statement request.

        statementType:
            6 = Financial Information
            7 = Financial Statements and Reports
            0 = Previous Balance Sheet
            1 = Previous Statement of Income
            2 = Previous Cash Flows
        """

        statement_name = self.STATEMENT_TYPES.get(
            statement_type,
            f"statement_type_{statement_type}",
        )

        self._clear_performance_logs()

        if statement_type == 6:
            self._click(
                By.ID,
                "unifiedResultBean",
            )

        elif statement_type == 7:
            self._click(
                By.ID,
                "finacialStatementAndReports",
            )

        elif statement_type == 0:
            self._click(
                By.ID,
                "balancesheet",
            )

        elif statement_type == 1:
            self._click(
                By.ID,
                "statementofincome",
            )

        elif statement_type == 2:
            self._click(
                By.ID,
                "cashflow",
            )

        else:
            raise ValueError(
                f"Unsupported statement type: "
                f"{statement_type}"
            )

        response = self._capture_statement(
            statement_type
        )

        if not response:
            raise RuntimeError(
                f"Could not capture "
                f"{statement_name} "
                f"(statementType={statement_type}) "
                f"for {symbol}"
            )

        return self._parse_statement_html(
            response,
            statement_type,
        )

    # ------------------------------------------------------------------
    # Previous periods
    # ------------------------------------------------------------------

    def _open_previous_periods(
        self,
    ) -> None:
        self._clear_performance_logs()

        self._click(
            By.CLASS_NAME,
            "displayPrevBtn",
        )

        time.sleep(2)

    # ------------------------------------------------------------------
    # Capture statement response
    # ------------------------------------------------------------------

    def _capture_statement(
        self,
        statement_type: int,
    ) -> str | None:
        """
        Capture the response belonging to
        NJstatementsTabData.

        We identify the response by statementType
        so that the correct request is returned.
        """

        target = (
            f"statementType={statement_type}"
        )

        deadline = time.time() + 10

        while time.time() < deadline:
            for entry in self.browser.driver.get_log(
                "performance"
            ):
                try:
                    message = (
                        __import__("json")
                        .loads(
                            entry["message"]
                        )["message"]
                    )
                except Exception:
                    continue

                if (
                    message.get("method")
                    != "Network.responseReceived"
                ):
                    continue

                response = message[
                    "params"
                ]["response"]

                url = response.get(
                    "url",
                    "",
                )

                if (
                    "NJstatementsTabData"
                    not in url
                ):
                    continue

                if target not in url:
                    continue

                request_id = (
                    message["params"]
                    .get("requestId")
                )

                if not request_id:
                    continue

                try:
                    body = (
                        self.browser.driver
                        .execute_cdp_cmd(
                            "Network.getResponseBody",
                            {
                                "requestId": request_id
                            },
                        )
                    )

                    return body.get(
                        "body"
                    )

                except Exception:
                    continue

            time.sleep(0.25)

        return None

    # ------------------------------------------------------------------
    # Financial HTML parser
    # ------------------------------------------------------------------

    def _parse_statement_html(
        self,
        html: str,
        statement_type: int,
    ):
        """
        Parse a statement HTML response into
        structured rows.
        """

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        if statement_type == 6:
            return self._parse_financial_information(
                soup
            )

        if statement_type == 7:
            return self._parse_financial_reports(
                soup
            )

        return self._parse_previous_statement(
            soup
        )

    # ------------------------------------------------------------------
    # Financial Information
    # ------------------------------------------------------------------

    def _parse_financial_information(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        """
        Parse Financial Information.

        Returns:
            {
                "balance_sheet": [],
                "statement_of_income": [],
                "cash_flows": [],
            }
        """

        result = {
            "balance_sheet": [],
            "statement_of_income": [],
            "cash_flows": [],
        }

        tables = soup.find_all("table")

        if not tables:
            return result

        table = tables[0]

        rows = table.find_all("tr")

        if not rows:
            return result

        current_statement = None
        periods = []

        statement_labels = {
            "balance sheet": "balance_sheet",
            "statement of income": "statement_of_income",
            "cash flows": "cash_flows",
            "cash flow": "cash_flows",
            "الميزانية العمومية": "balance_sheet",
            "قائمة المركز المالي": "balance_sheet",
            "قائمة الدخل": "statement_of_income",
            "التدفقات النقدية": "cash_flows",
            "قائمة التدفق النقدي": "cash_flows",
        }

        ignored_labels = {
            "All Figures in",
            "All Figures are in",
            "All Currency In",
            "Last Update Date",
            "جميع الأرقام بال",
            "جميع الأرقام في",
            "العملة في",
            "تاريخ آخر تحديث",
        }

        for row in rows:
            cells = row.find_all(
                ["th", "td"]
            )

            values = [
                self._clean_text(
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                )
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

            if (
                normalized_first_value
                in statement_labels
            ):
                current_statement = (
                    statement_labels[
                        normalized_first_value
                    ]
                )

                periods = [
                    value
                    for value in values[1:]
                    if value
                    and self._looks_like_date(
                        value
                    )
                ]

                continue

            if first_value in ignored_labels:
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

                value = values[index]

                result[
                    current_statement
                ].append(
                    {
                        "period": period,
                        "metric": metric,
                        "value": self._parse_numeric_value(
                            value
                        ),
                    }
                )

        return result

    # ------------------------------------------------------------------
    # Financial Statements and Reports
    # ------------------------------------------------------------------

    def _parse_financial_reports(
        self,
        soup: BeautifulSoup,
    ) -> list[dict]:
        table = soup.find(
            "table",
            id="sukuk-xbrl",
        )

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
                current_section = self._clean_text(
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

            period = self._clean_text(
                cells[0].get_text(
                    " ",
                    strip=True,
                )
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

                # The publication date belongs to the
                # report cell, not necessarily to the
                # <a> element.
                #
                # For PDF reports, the date may be
                # inside the <a>.
                #
                # For XBRL reports, the date is outside
                # the <a>, directly inside the <td>.
                cell_text = self._clean_text(
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                )

                date_match = re.search(
                    r"\b\d{4}-\d{2}-\d{2}\b",
                    cell_text,
                )

                if date_match:
                    publication_date = (
                        date_match.group(0)
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
                            "publication_date": (
                                publication_date
                            ),
                            "file_type": (
                                self._get_file_type(
                                    href
                                )
                            ),
                            "file_url": (
                                self._build_profile_url(
                                    href
                                )
                            ),
                        }
                    )

        return reports

    @staticmethod
    def _get_file_type(
        href: str,
    ) -> str:
        href_lower = href.lower()

        if href_lower.endswith(".pdf"):
            return "pdf"

        if href_lower.endswith(".xls"):
            return "xls"

        if href_lower.endswith(".xlsx"):
            return "xlsx"

        if href_lower.endswith(".html"):
            return "html"

        return "unknown"

    # ------------------------------------------------------------------
    # Previous Financial Statements
    # ------------------------------------------------------------------

    def _parse_previous_statement(
        self,
        soup: BeautifulSoup,
    ) -> list[dict]:
        """
        Parse a previous-period financial statement.

        Each row has:
            period
            metric
            value
        """

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
                text = self._clean_text(
                    header.get_text(
                        " ",
                        strip=True,
                    )
                )

                if text:
                    periods.append(text)

            if periods:
                break

        if not periods:
            return []

        records = []

        ignored_labels = {
            "All Figures in",
            "All Figures are in",
            "All Currency In",
            "Last Update Date",
            "جميع الأرقام بال",
            "جميع الأرقام في",
            "العملة في",
            "تاريخ آخر تحديث",
        }

        for row in rows:
            cells = row.find_all("td")

            if len(cells) < 2:
                continue

            metric = self._clean_text(
                cells[0].get_text(
                    " ",
                    strip=True,
                )
            )

            if not metric:
                continue

            if metric in ignored_labels:
                continue

            values = []

            for cell in cells[1:]:
                value = self._clean_text(
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                )

                values.append(
                    self._parse_numeric_value(
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

    # ------------------------------------------------------------------
    # Financial helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_numeric_value(
        value: str,
    ):
        if not value or value == "-":
            return None

        value_without_commas = (
            value.replace(
                ",",
                "",
            )
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
    def _extract_table_headers(
        table,
    ) -> list[str]:
        header_rows = table.find_all(
            "tr"
        )

        for row in header_rows:
            cells = row.find_all("th")

            if not cells:
                continue

            headers = [
                SukukScraper._clean_text(
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                )
                for cell in cells
            ]

            if headers:
                return headers

        return []

    @staticmethod
    def _looks_like_date(
        value: str,
    ) -> bool:
        if re.fullmatch(
            r"\d{4}",
            value,
        ):
            return True

        if re.fullmatch(
            r"\d{4}-\d{2}-\d{2}",
            value,
        ):
            return True

        if re.fullmatch(
            r"\d{4}/\d{2}/\d{2}",
            value,
        ):
            return True

        return False

    # ------------------------------------------------------------------
    # Browser helpers
    # ------------------------------------------------------------------

    def _click(
        self,
        by: By,
        selector: str,
    ) -> None:
        element = self.browser.driver.find_element(
            by,
            selector,
        )

        self.browser.driver.execute_script(
            "arguments[0].click();",
            element,
        )

        time.sleep(1)

    def _clear_performance_logs(
        self,
    ) -> None:
        try:
            self.browser.driver.get_log(
                "performance"
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(
        value: str,
    ) -> str:
        if value is None:
            return ""

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