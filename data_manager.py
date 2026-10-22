# 個人記帳分析系統 - 第 21 階段
# 集中管理 CSV 讀取、儲存及資料驗證

import csv
import os
import tempfile
from pathlib import Path
from datetime import datetime


# ==============================
# 1. 基本設定
# ==============================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FILE_PATH = DATA_DIR / "records.csv"

FIELDNAMES = [
    "date",
    "type",
    "category",
    "item",
    "amount"
]


# ==============================
# 2. 驗證日期
# ==============================

def validate_date(date_string):

    try:
        parsed_date = datetime.strptime(
            date_string,
            "%Y-%m-%d"
        )

        return (
            parsed_date.strftime("%Y-%m-%d")
            == date_string
        )

    except (ValueError, TypeError):
        return False


# ==============================
# 3. 驗證記帳資料
# ==============================

def validate_record(record):

    if not isinstance(record, dict):
        raise ValueError("記帳資料必須是字典。")

    # 確認欄位完整
    for field in FIELDNAMES:
        if field not in record:
            raise ValueError(
                f"缺少必要欄位：{field}"
            )

    # 日期
    date = str(record["date"]).strip()

    if not validate_date(date):
        raise ValueError(
            "日期格式錯誤，請使用 YYYY-MM-DD。"
        )

    # 類型
    record_type = str(
        record["type"]
    ).strip()

    if record_type not in ["收入", "支出"]:
        raise ValueError(
            "類型只能是收入或支出。"
        )

    # 分類
    category = str(
        record["category"]
    ).strip()

    if not category:
        raise ValueError("分類不能留空。")

    # 項目
    item = str(
        record["item"]
    ).strip()

    if not item:
        raise ValueError("項目不能留空。")

    # 金額
    raw_amount = record["amount"]

    if isinstance(raw_amount, bool):
        raise ValueError("金額必須是正整數。")

    if not isinstance(raw_amount, (str, int)):
        raise ValueError("金額必須是正整數。")

    try:
        amount = int(raw_amount)
    except (ValueError, TypeError):
        raise ValueError(
            "金額必須是正整數。"
        )

    if amount <= 0:
        raise ValueError(
            "金額必須大於 0。"
        )

    # 避免把 12.5 這類文字當成整數
    if isinstance(raw_amount, str):
        if not raw_amount.strip().isdigit():
            raise ValueError(
                "金額必須是正整數。"
            )

    # 回傳整理過的資料
    return {
        "date": date,
        "type": record_type,
        "category": category,
        "item": item,
        "amount": amount
    }


# ==============================
# 4. 讀取所有記帳資料
# ==============================

def load_records():

    records = []

    if (
        not FILE_PATH.exists()
        or FILE_PATH.stat().st_size == 0
    ):
        return records

    with open(
        FILE_PATH,
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row_number, row in enumerate(
            reader,
            start=2
        ):
            try:
                record = validate_record(row)

            except ValueError as error:
                raise ValueError(
                    f"CSV 第 {row_number} 行資料錯誤："
                    f"{error}"
                ) from error

            records.append(record)

    return records


# ==============================
# 5. 安全儲存所有記帳資料
# ==============================

def save_all_records(records):

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 儲存前先驗證所有紀錄
    validated_records = [
        validate_record(record)
        for record in records
    ]

    temp_path = None

    try:
        # 先建立暫存檔
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=DATA_DIR,
            suffix=".tmp",
            delete=False
        ) as file:

            temp_path = file.name

            writer = csv.DictWriter(
                file,
                fieldnames=FIELDNAMES
            )

            writer.writeheader()
            writer.writerows(validated_records)

        # 成功寫入後，取代原本 CSV
        os.replace(
            temp_path,
            FILE_PATH
        )

    finally:
        # 清除未使用的暫存檔
        if (
            temp_path is not None
            and os.path.exists(temp_path)
        ):
            os.remove(temp_path)


# ==============================
# 6. 新增一筆記帳資料
# ==============================

def add_record_to_csv(record):

    validated_record = validate_record(record)

    # 先讀取既有資料
    records = load_records()

    # 加入新資料
    records.append(validated_record)

    # 儲存全部資料
    save_all_records(records)


# ==============================
# 7. 修改指定記帳資料
# ==============================

def update_record(index, updated_record):

    records = load_records()

    if not 0 <= index < len(records):
        raise IndexError(
            "找不到指定的記帳紀錄。"
        )

    records[index] = validate_record(
        updated_record
    )

    save_all_records(records)


# ==============================
# 8. 刪除指定記帳資料
# ==============================

def delete_record_from_csv(index):

    records = load_records()

    if not 0 <= index < len(records):
        raise IndexError(
            "找不到指定的記帳紀錄。"
        )

    del records[index]

    save_all_records(records)
