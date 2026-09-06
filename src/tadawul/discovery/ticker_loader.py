from __future__ import annotations

import json
from pathlib import Path


class TickerLoader:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> list[dict]:
        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def get_by_symbol(self, symbol: str) -> dict | None:
        companies = self.load()

        for company in companies:
            if company.get("company") == symbol:
                return company

        return None