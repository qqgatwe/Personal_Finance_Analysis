
"""第 29 階段：規則式智慧財務分析。"""

import pandas as pd


def previous_month(month):
    year, number = map(int, month.split("-"))
    if number == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{number - 1:02d}"


def monthly_totals(df, month):
    data = df[df["month"] == month]
    income = float(
        data.loc[data["type"] == "收入", "amount"].sum()
    )
    expense = float(
        data.loc[data["type"] == "支出", "amount"].sum()
    )
    return {
        "收入": income,
        "支出": expense,
        "結餘": income - expense,
    }


def compare_months(df, month):
    previous = previous_month(month)
    current = monthly_totals(df, month)
    prior = monthly_totals(df, previous)

    rows = []

    for metric in ["收入", "支出", "結餘"]:
        this_value = current[metric]
        last_value = prior[metric]
        change = this_value - last_value

        percent = (
            change / abs(last_value) * 100
            if last_value != 0
            else None
        )

        rows.append({
            "指標": metric,
            "本月": this_value,
            "上月": last_value,
            "增減金額": change,
            "變化率(%)": percent,
        })

    return pd.DataFrame(rows)


def category_comparison(df, month):
    previous = previous_month(month)

    expenses = df[
        (df["type"] == "支出")
        & (df["month"].isin([month, previous]))
    ]

    if expenses.empty:
        return pd.DataFrame(columns=[
            "分類", "本月", "上月",
            "增減金額", "變化率(%)",
        ])

    grouped = (
        expenses.groupby(["category", "month"])["amount"]
        .sum()
        .unstack(fill_value=0)
    )

    current = (
        grouped[month]
        if month in grouped.columns
        else pd.Series(0, index=grouped.index)
    )

    prior = (
        grouped[previous]
        if previous in grouped.columns
        else pd.Series(0, index=grouped.index)
    )

    result = pd.DataFrame({
        "分類": grouped.index,
        "本月": current.values,
        "上月": prior.values,
    })

    result["增減金額"] = (
        result["本月"] - result["上月"]
    )

    result["變化率(%)"] = result.apply(
        lambda row: (
            row["增減金額"] / row["上月"] * 100
            if row["上月"] > 0
            else None
        ),
        axis=1,
    )

    return result.sort_values(
        "增減金額",
        ascending=False,
    ).reset_index(drop=True)


def build_insights(df, month, budgets=None):
    """依實際收支與預算產生文字提醒。"""
    budgets = budgets or []

    previous = previous_month(month)
    current = monthly_totals(df, month)
    prior = monthly_totals(df, previous)

    has_current = bool(
        (df["month"] == month).any()
    )
    has_prior = bool(
        (df["month"] == previous).any()
    )

    messages = []

    if not has_current:
        return [(
            "info",
            "選定月份沒有記帳資料，尚無法分析收支。",
        )]

    if current["結餘"] < 0:
        messages.append((
            "error",
            f"本月支出超過收入 "
            f"NT$ {abs(current['結餘']):,.0f}。",
        ))
    elif current["收入"] > 0:
        rate = (
            current["結餘"] / current["收入"] * 100
        )
        messages.append((
            "success",
            f"本月結餘 NT$ {current['結餘']:,.0f}，"
            f"儲蓄率 {rate:.1f}%。",
        ))

    if has_prior:
        difference = (
            current["支出"] - prior["支出"]
        )

        if difference > 0:
            messages.append((
                "warning",
                f"本月支出比上月增加 "
                f"NT$ {difference:,.0f}。",
            ))
        elif difference < 0:
            messages.append((
                "success",
                f"本月支出比上月減少 "
                f"NT$ {abs(difference):,.0f}。",
            ))

        changes = category_comparison(df, month)
        increases = changes[
            changes["增減金額"] > 0
        ]

        if not increases.empty:
            top = increases.iloc[0]
            messages.append((
                "info",
                f"支出增加最多的分類是"
                f"「{top['分類']}」，增加 "
                f"NT$ {top['增減金額']:,.0f}。",
            ))
    else:
        messages.append((
            "info",
            "上個月沒有記帳紀錄，"
            "因此不顯示月增減結論。",
        ))

    spending = (
        df[
            (df["month"] == month)
            & (df["type"] == "支出")
        ]
        .groupby("category")["amount"]
        .sum()
        .to_dict()
    )

    for row in budgets:
        if row["month"] != month:
            continue

        category = row["category"]
        budget = row["budget"]
        amount = spending.get(category, 0)

        if amount > budget:
            messages.append((
                "error",
                f"「{category}」超出預算 "
                f"NT$ {amount - budget:,.0f}。",
            ))
        elif amount >= budget * 0.8:
            messages.append((
                "warning",
                f"「{category}」已使用 "
                f"{amount / budget:.0%} 的預算。",
            ))

    return messages
