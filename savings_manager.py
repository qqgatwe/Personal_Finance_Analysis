
"""第 31 階段：儲蓄目標與存款紀錄管理。"""

import csv
import os
import tempfile
import uuid
from datetime import date, datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

GOALS_FILE = DATA_DIR / "savings_goals.csv"
DEPOSITS_FILE = DATA_DIR / "savings_deposits.csv"

GOAL_FIELDS = [
    "goal_id",
    "name",
    "target_amount",
    "target_date",
    "created_date",
]

DEPOSIT_FIELDS = [
    "deposit_id",
    "goal_id",
    "date",
    "amount",
    "note",
]


def _positive_int(value, label="金額"):
    if isinstance(value, bool):
        raise ValueError(f"{label}必須為正整數")

    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label}必須為正整數")

    if number <= 0:
        raise ValueError(f"{label}必須大於 0")

    if str(value).strip() != str(number):
        raise ValueError(f"{label}必須為正整數")

    return number


def _date_string(value):
    if isinstance(value, datetime):
        value = value.date()

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    try:
        parsed = datetime.strptime(
            str(value),
            "%Y-%m-%d",
        )
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("日期格式必須為 YYYY-MM-DD")


def _read_csv(path, fields):
    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(
                f"{path.name} 缺少欄位名稱"
            )

        if not set(fields).issubset(reader.fieldnames):
            raise ValueError(
                f"{path.name} 欄位格式不正確"
            )

        return list(reader)


def _write_csv(path, fields, rows):
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=DATA_DIR,
            suffix=".tmp",
            delete=False,
        ) as file:
            temp_path = Path(file.name)

            writer = csv.DictWriter(
                file,
                fieldnames=fields,
            )

            writer.writeheader()
            writer.writerows(rows)

        os.replace(temp_path, path)

    finally:
        if (
            temp_path is not None
            and temp_path.exists()
        ):
            temp_path.unlink()


def load_goals():
    rows = _read_csv(
        GOALS_FILE,
        GOAL_FIELDS,
    )

    goals = []

    for row in rows:
        goals.append({
            "goal_id": row["goal_id"],
            "name": row["name"],
            "target_amount": _positive_int(
                row["target_amount"],
                "目標金額",
            ),
            "target_date": _date_string(
                row["target_date"]
            ),
            "created_date": _date_string(
                row["created_date"]
            ),
        })

    return goals


def load_deposits():
    rows = _read_csv(
        DEPOSITS_FILE,
        DEPOSIT_FIELDS,
    )

    deposits = []

    for row in rows:
        deposits.append({
            "deposit_id": row["deposit_id"],
            "goal_id": row["goal_id"],
            "date": _date_string(
                row["date"]
            ),
            "amount": _positive_int(
                row["amount"],
                "存款金額",
            ),
            "note": row["note"],
        })

    return deposits


def create_goal(
    name,
    target_amount,
    target_date,
):
    name = str(name).strip()

    if not name:
        raise ValueError("目標名稱不能空白")

    target_amount = _positive_int(
        target_amount,
        "目標金額",
    )

    target_date = _date_string(
        target_date
    )

    goals = load_goals()

    goal = {
        "goal_id": uuid.uuid4().hex,
        "name": name,
        "target_amount": target_amount,
        "target_date": target_date,
        "created_date": date.today().strftime(
            "%Y-%m-%d"
        ),
    }

    goals.append(goal)

    _write_csv(
        GOALS_FILE,
        GOAL_FIELDS,
        goals,
    )

    return goal


def update_goal(
    goal_id,
    name,
    target_amount,
    target_date,
):
    name = str(name).strip()

    if not name:
        raise ValueError("目標名稱不能空白")

    target_amount = _positive_int(
        target_amount,
        "目標金額",
    )

    target_date = _date_string(
        target_date
    )

    goals = load_goals()

    for goal in goals:
        if goal["goal_id"] == goal_id:
            goal["name"] = name
            goal["target_amount"] = target_amount
            goal["target_date"] = target_date

            _write_csv(
                GOALS_FILE,
                GOAL_FIELDS,
                goals,
            )

            return goal

    raise ValueError("找不到指定的儲蓄目標")


def add_deposit(
    goal_id,
    deposit_date,
    amount,
    note="",
):
    goals = load_goals()

    if not any(
        goal["goal_id"] == goal_id
        for goal in goals
    ):
        raise ValueError("找不到指定的儲蓄目標")

    amount = _positive_int(
        amount,
        "存款金額",
    )

    deposit = {
        "deposit_id": uuid.uuid4().hex,
        "goal_id": goal_id,
        "date": _date_string(
            deposit_date
        ),
        "amount": amount,
        "note": str(note).strip(),
    }

    deposits = load_deposits()
    deposits.append(deposit)

    _write_csv(
        DEPOSITS_FILE,
        DEPOSIT_FIELDS,
        deposits,
    )

    return deposit


def delete_deposit(deposit_id):
    deposits = load_deposits()

    remaining = [
        row
        for row in deposits
        if row["deposit_id"] != deposit_id
    ]

    if len(remaining) == len(deposits):
        raise ValueError("找不到指定的存款紀錄")

    _write_csv(
        DEPOSITS_FILE,
        DEPOSIT_FIELDS,
        remaining,
    )


def delete_goal(goal_id):
    goals = load_goals()

    remaining_goals = [
        goal
        for goal in goals
        if goal["goal_id"] != goal_id
    ]

    if len(remaining_goals) == len(goals):
        raise ValueError("找不到指定的儲蓄目標")

    # 先更新存款紀錄，再刪除目標。
    # 兩個 CSV 並非資料庫交易，請定期備份。
    deposits = load_deposits()

    remaining_deposits = [
        row
        for row in deposits
        if row["goal_id"] != goal_id
    ]

    _write_csv(
        DEPOSITS_FILE,
        DEPOSIT_FIELDS,
        remaining_deposits,
    )

    _write_csv(
        GOALS_FILE,
        GOAL_FIELDS,
        remaining_goals,
    )


def get_goal_progress(goal, deposits):
    saved = sum(
        row["amount"]
        for row in deposits
        if row["goal_id"] == goal["goal_id"]
    )

    target = goal["target_amount"]

    remaining = max(
        target - saved,
        0,
    )

    progress = saved / target

    return {
        "saved": saved,
        "target": target,
        "remaining": remaining,
        "progress": progress,
        "completed": saved >= target,
    }


def get_monthly_required(goal, deposits):
    """估算從目前月份到截止月份，每月需存金額。"""

    progress = get_goal_progress(
        goal,
        deposits,
    )

    if progress["completed"]:
        return 0

    today = date.today()

    target_date = datetime.strptime(
        goal["target_date"],
        "%Y-%m-%d",
    ).date()

    if target_date < today:
        return None

    months = (
        (target_date.year - today.year) * 12
        + target_date.month
        - today.month
        + 1
    )

    return (
        progress["remaining"] + months - 1
    ) // months
