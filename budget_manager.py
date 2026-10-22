
"""每月分類預算的 CSV 儲存模組。"""

import csv
import os
import re
import tempfile
from pathlib import Path


BUDGET_FILE = (
    Path(__file__).resolve().parent
    / "data"
    / "budgets.csv"
)

FIELDS = ["month", "category", "budget"]


def _validate(month, category, amount=None):
    if not re.fullmatch(
        r"\d{4}-(0[1-9]|1[0-2])",
        str(month),
    ):
        raise ValueError("月份格式必須為 YYYY-MM")

    category = str(category).strip()

    if not category:
        raise ValueError("分類不可空白")

    if amount is not None:
        if (
            not isinstance(amount, int)
            or isinstance(amount, bool)
            or amount <= 0
        ):
            raise ValueError(
                "預算金額必須為正整數"
            )

    return str(month), category


def load_budgets():
    if not BUDGET_FILE.exists():
        return []

    with BUDGET_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if (
            not reader.fieldnames
            or not set(FIELDS).issubset(
                reader.fieldnames
            )
        ):
            raise ValueError(
                "budgets.csv 欄位不正確"
            )

        results = []

        for row in reader:
            month, category = _validate(
                row["month"],
                row["category"],
            )

            amount = int(row["budget"])

            _validate(
                month,
                category,
                amount,
            )

            results.append({
                "month": month,
                "category": category,
                "budget": amount,
            })

        return results


def _save_budgets(rows):
    BUDGET_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8-sig",
            newline="",
            dir=BUDGET_FILE.parent,
            delete=False,
            suffix=".tmp",
        ) as file:
            temp_path = Path(file.name)

            writer = csv.DictWriter(
                file,
                fieldnames=FIELDS,
            )

            writer.writeheader()
            writer.writerows(rows)

        os.replace(
            temp_path,
            BUDGET_FILE,
        )

    finally:
        if (
            temp_path is not None
            and temp_path.exists()
        ):
            temp_path.unlink()


def upsert_budget(month, category, amount):
    month, category = _validate(
        month,
        category,
        amount,
    )

    rows = load_budgets()

    for row in rows:
        if (
            row["month"] == month
            and row["category"] == category
        ):
            row["budget"] = amount
            _save_budgets(rows)
            return

    rows.append({
        "month": month,
        "category": category,
        "budget": amount,
    })

    _save_budgets(rows)


def delete_budget(month, category):
    month, category = _validate(
        month,
        category,
    )

    rows = load_budgets()

    remaining = [
        row
        for row in rows
        if (
            row["month"],
            row["category"],
        ) != (
            month,
            category,
        )
    ]

    if len(remaining) == len(rows):
        raise ValueError(
            "找不到指定的預算"
        )

    _save_budgets(remaining)
