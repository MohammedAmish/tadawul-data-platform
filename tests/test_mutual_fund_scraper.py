"""Test mutual fund scraper parsing logic against saved HTML."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup


HTML_FILE = Path("data/mutual_fund_profile_test.html")


def test_parse_fund_info():
    """Test parsing fund info table from saved HTML."""
    html = HTML_FILE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    containers = soup.find_all("div", class_="fundInfo")
    visible_container = containers[0] if containers else None

    assert visible_container is not None, "Fund info container not found"

    table = visible_container.find("table", id="issuerTable")
    assert table is not None, "Fund info table not found"

    rows = table.find_all("tr")
    fund_info = {}

    for row in rows:
        cells = row.find_all("td")

        if len(cells) < 2:
            continue

        label = cells[0].get_text(strip=True)
        value = cells[1].get_text(strip=True)

        fund_info[label] = value

    assert fund_info.get("Fund Name") == "SNB Capital Saudi Riyal Trade Fund"
    assert fund_info.get("Fund Info") == "Capital Preservation"
    assert fund_info.get("Fund Manager") == "SNB Capital"
    assert fund_info.get("Telephone") == "018747106"
    assert "alahlicapital.com" in fund_info.get("Website", "")


def test_parse_market():
    """Test parsing market from saved HTML."""
    html = HTML_FILE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    market_element = soup.select_one("div.market_capital ul li")
    assert market_element is not None, "Market element not found"

    market = market_element.get_text(strip=True)
    assert market == "Mutual Funds"


def test_parse_terms_and_conditions():
    """Test parsing Terms and Conditions documents."""
    html = HTML_FILE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    pdf_boxes = soup.find_all("div", class_="pdfDwlBox")
    terms_docs = []

    for box in pdf_boxes:
        header = box.find("h4")

        if not header:
            continue

        header_text = header.get_text(strip=True)

        if "Terms and Conditions" not in header_text:
            continue

        year_box = box.find("div", class_="yearPdfDwl")

        if not year_box:
            continue

        links = year_box.find_all("a", class_="btn-pdf")

        for link in links:
            href = link.get("href", "")
            date_elem = link.find_next("strong")
            date_text = (
                date_elem.get_text(strip=True)
                if date_elem
                else None
            )

            terms_docs.append({
                "url": href,
                "date": date_text,
            })

    assert len(terms_docs) > 0, "No Terms and Conditions documents found"
    assert "/Resources/mfpdfs/terms/" in terms_docs[0]["url"]
    assert terms_docs[0]["date"] == "2024-10-13"


def test_parse_financial_statements():
    """Test parsing Financial Statements documents."""
    html = HTML_FILE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    heading = soup.find(
        "h4",
        class_="subHdng",
        string=lambda t: t and "Financial Statements" in t,
    )

    assert heading is not None, "Financial Statements heading not found"

    table_div = heading.find_next("div", class_="financial_table")
    assert table_div is not None, "Financial table not found"

    table = table_div.find("table")
    assert table is not None, "Table not found"

    links = table_div.find_all("a", class_="btn-pdf")
    assert len(links) > 0, "No Financial Statement PDFs found"

    first_href = links[0].get("href", "")
    assert "/Resources/mfpdfs/stmt/" in first_href


def test_parse_voting_policy():
    """Test parsing Voting Policy documents."""
    html = HTML_FILE.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    pdf_boxes = soup.find_all("div", class_="pdfDwlBox")
    voting_docs = []

    for box in pdf_boxes:
        header = box.find("h4")

        if not header:
            continue

        header_text = header.get_text(strip=True)

        if "Voting Policy" not in header_text:
            continue

        year_box = box.find("div", class_="yearPdfDwl")

        if not year_box:
            continue

        links = year_box.find_all("a", class_="btn-pdf")

        for link in links:
            href = link.get("href", "")
            date_elem = link.find_next("strong")
            date_text = (
                date_elem.get_text(strip=True)
                if date_elem
                else None
            )

            voting_docs.append({
                "url": href,
                "date": date_text,
            })

    assert len(voting_docs) > 0, "No Voting Policy documents found"
    assert "2023-02-08" in voting_docs[0]["date"]


if __name__ == "__main__":
    test_parse_market()
    print("[PASS] test_parse_market")

    test_parse_fund_info()
    print("[PASS] test_parse_fund_info")

    test_parse_terms_and_conditions()
    print("[PASS] test_parse_terms_and_conditions")

    test_parse_financial_statements()
    print("[PASS] test_parse_financial_statements")

    test_parse_voting_policy()
    print("[PASS] test_parse_voting_policy")

    print("\nAll tests passed!")
