
"""第 32 階段：每月財務報告資料整理。"""

from datetime import date
import pandas as pd


def build_monthly_report(
    records_df,
    month,
    budgets,
    goals,
    deposits,
):
    """整理指定月份的完整財務報告資料。"""

    # 確保不會修改 Dashboard 原始資料
    df = records_df.copy()

    if not df.empty:
        df["date"] = pd.to_datetime(
            df["date"], errors="raise"
        )
        df["amount"] = pd.to_numeric(
            df["amount"], errors="raise"
        )
        df["month"] = df["date"].dt.strftime(
            "%Y-%m"
        )

    current = df[
        df["month"] == month
    ].copy()

    income = float(
        current.loc[
            current["type"] == "收入",
            "amount",
        ].sum()
    )

    expense = float(
        current.loc[
            current["type"] == "支出",
            "amount",
        ].sum()
    )

    balance = income - expense

    savings_rate = (
        balance / income * 100
        if income > 0 else None
    )

    # 支出分類統計
    expenses = current[
        current["type"] == "支出"
    ]

    category_series = (
        expenses.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    categories = []

    for category, amount in category_series.items():
        categories.append({
            "category": str(category),
            "amount": float(amount),
            "percentage": (
                float(amount) / expense * 100
                if expense > 0 else 0
            ),
        })

    # 當月預算
    budget_rows = []

    for budget in budgets:
        if budget["month"] != month:
            continue

        category = budget["category"]
        limit = float(budget["budget"])
        spent = float(
            category_series.get(category, 0)
        )

        budget_rows.append({
            "category": category,
            "budget": limit,
            "spent": spent,
            "remaining": limit - spent,
            "percentage": (
                spent / limit * 100
                if limit > 0 else 0
            ),
        })

    # 儲蓄目標採「報告月份月底」快照
    # 不把未來的存款算進過去月份
    period_end = pd.Period(
        month, freq="M"
    ).end_time.date()

    savings_rows = []

    for goal in goals:
        created = date.fromisoformat(
            goal["created_date"]
        )

        if created > period_end:
            continue

        saved = sum(
            float(deposit["amount"])
            for deposit in deposits
            if (
                deposit["goal_id"] == goal["goal_id"]
                and date.fromisoformat(
                    deposit["date"]
                ) <= period_end
            )
        )

        target = float(
            goal["target_amount"]
        )

        savings_rows.append({
            "name": goal["name"],
            "target": target,
            "saved": saved,
            "remaining": max(
                target - saved, 0
            ),
            "percentage": (
                saved / target * 100
                if target > 0 else 0
            ),
            "target_date": goal["target_date"],
        })

    # 規則式財務建議
    insights = []

    if current.empty:
        insights.append(
            "本月尚無記帳資料，建議持續記錄收入與支出。"
        )
    elif income <= 0:
        insights.append(
            "本月沒有收入紀錄，請確認是否漏記。"
        )
    elif balance < 0:
        insights.append(
            "本月支出高於收入，建議檢查主要支出分類。"
        )
    elif savings_rate is not None:
        if savings_rate >= 20:
            insights.append(
                "本月儲蓄率達 20% 以上，財務結餘表現良好。"
            )
        else:
            insights.append(
                "本月儲蓄率低於 20%，可評估非必要支出。"
            )

    if categories:
        largest = categories[0]
        insights.append(
            f"本月最大支出分類為"
            f"「{largest['category']}」，"
            f"占總支出 {largest['percentage']:.1f}%。"
        )

    for row in budget_rows:
        if row["spent"] > row["budget"]:
            insights.append(
                f"「{row['category']}」已超出預算 "
                f"NT$ {abs(row['remaining']):,.0f}。"
            )
        elif row["percentage"] >= 80:
            insights.append(
                f"「{row['category']}」預算使用率"
                f"已達 {row['percentage']:.1f}%。"
            )

    # 記帳明細
    transactions = []

    for _, row in current.sort_values(
        "date",
        ascending=True,
    ).iterrows():
        transactions.append({
            "date": row["date"].strftime(
                "%Y-%m-%d"
            ),
            "type": str(row["type"]),
            "category": str(row["category"]),
            "item": str(row["item"]),
            "amount": float(row["amount"]),
        })

    return {
        "month": month,
        "income": income,
        "expense": expense,
        "balance": balance,
        "savings_rate": savings_rate,
        "record_count": len(current),
        "categories": categories,
        "budgets": budget_rows,
        "savings_goals": savings_rows,
        "insights": insights,
        "transactions": transactions,
    }
