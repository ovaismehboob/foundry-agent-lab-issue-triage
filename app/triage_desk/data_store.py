"""Loads the synthetic JSON data that ships with the lab."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from triage_desk.models import Customer, Issue


class DataStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)

    def _read(self, name: str) -> dict:
        path = self.data_dir / name
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    @property
    def taxonomy(self) -> dict:
        return self._read("taxonomy.json")

    @property
    def routing_rules(self) -> dict:
        return self._read("routing_rules.json")

    def issues(self) -> list[Issue]:
        return [Issue(**item) for item in self._read("incoming_issues.json")["issues"]]

    def customers(self) -> dict[str, Customer]:
        return {item["customer_id"]: Customer(**item) for item in self._read("customers.json")["customers"]}

    def get_issue(self, issue_id: str) -> Issue | None:
        wanted = issue_id.strip().upper()
        return next((issue for issue in self.issues() if issue.issue_id == wanted), None)

    def get_customer(self, customer_id: str | None) -> Customer | None:
        if not customer_id:
            return None
        return self.customers().get(customer_id.strip().upper())


@lru_cache(maxsize=4)
def get_store(data_dir: str) -> DataStore:
    return DataStore(Path(data_dir))
