import json
from pathlib import Path
from typing import Any


class TickerLoader:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> list[dict[str, Any]]:
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("tickerData.json must contain a JSON array")

        return data

    def get_company(self, symbol: str) -> dict[str, Any]:
        companies = self.load()

        for company in companies:
            if str(company.get("company")) == str(symbol):
                return company

        raise ValueError(f"Company {symbol} not found")