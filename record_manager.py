
"""第 30 階段：記帳紀錄的搜尋、篩選與排序。"""

import pandas as pd


def filter_records(
    df,
    keyword="",
    start_date=None,
    end_date=None,
    record_type="全部",
    categories=None,
    min_amount=None,
    max_amount=None,
    sort_by="日期：新到舊",
):
    """傳回篩選後的 DataFrame，不修改原始資料。"""

    result = df.copy()

    if result.empty:
        return result

    # 搜尋日期、分類、項目
    keyword = str(keyword or "").strip()

    if keyword:
        date_text = result["date"].dt.strftime("%Y-%m-%d")

        searchable = (
            date_text.fillna("")
            + " "
            + result["type"].fillna("").astype(str)
            + " "
            + result["category"].fillna("").astype(str)
            + " "
            + result["item"].fillna("").astype(str)
        )

        result = result[
            searchable.str.contains(
                keyword,
                case=False,
                regex=False,
                na=False,
            )
        ]

    # 日期區間
    if start_date is not None:
        result = result[
            result["date"].dt.date >= start_date
        ]

    if end_date is not None:
        result = result[
            result["date"].dt.date <= end_date
        ]

    # 收支類型
    if record_type in ("收入", "支出"):
        result = result[
            result["type"] == record_type
        ]

    # 多選分類
    if categories:
        result = result[
            result["category"].isin(categories)
        ]

    # 金額範圍
    if min_amount is not None:
        result = result[
            result["amount"] >= min_amount
        ]

    if max_amount is not None:
        result = result[
            result["amount"] <= max_amount
        ]

    # 排序
    sort_options = {
        "日期：新到舊": ("date", False),
        "日期：舊到新": ("date", True),
        "金額：高到低": ("amount", False),
        "金額：低到高": ("amount", True),
        "分類：A 到 Z": ("category", True),
    }

    column, ascending = sort_options.get(
        sort_by,
        ("date", False),
    )

    return result.sort_values(
        column,
        ascending=ascending,
        kind="stable",
    ).reset_index(drop=True)


def records_to_csv(df):
    """將目前篩選結果轉成 Excel 可讀取的 CSV。"""

    columns = [
        "date",
        "type",
        "category",
        "item",
        "amount",
    ]

    export_df = df[columns].copy()

    export_df["date"] = export_df["date"].dt.strftime(
        "%Y-%m-%d"
    )

    export_df.columns = [
        "日期",
        "類型",
        "分類",
        "項目",
        "金額",
    ]

    return export_df.to_csv(
        index=False,
    ).encode("utf-8-sig")
