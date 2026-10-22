
"""個人財務管理系統 Dashboard - 第 32 階段整合版。"""

from datetime import date
from html import escape

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from data_manager import (
    load_records,
    add_record_to_csv,
    update_record,
    delete_record_from_csv,
)
from budget_manager import (
    load_budgets,
    upsert_budget,
    delete_budget,
)
from insights import (
    previous_month,
    compare_months,
    category_comparison,
    build_insights,
)
from record_manager import (
    filter_records,
    records_to_csv,
)
from savings_manager import (
    load_goals,
    load_deposits,
    create_goal,
    update_goal,
    delete_goal,
    add_deposit,
    delete_deposit,
    get_goal_progress,
    get_monthly_required,
)
from report_manager import build_monthly_report
from report_exporter import export_pdf, export_excel


# ==========================================
# 1. 頁面設定
# ==========================================

st.set_page_config(
    page_title="個人財務管理系統",
    page_icon="💰",
    layout="wide",
)

GREEN = "#16866B"
RED = "#D35D61"
BLUE = "#4A8DB7"
ORANGE = "#D9A24A"

plt.rcParams["font.sans-serif"] = [
    "Microsoft JhengHei",
    "Microsoft YaHei",
    "Noto Sans CJK TC",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def apply_style():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #F6F8FB;
        }

        .block-container {
            max-width: 1450px;
            padding-top: 1.5rem;
        }

        [data-testid="stSidebar"] {
            background-color: #EDF2F7;
        }

        .summary-card {
            background: white;
            padding: 22px;
            border: 1px solid #E2E9F1;
            border-radius: 16px;
        }

        .summary-label {
            color: #64748B;
            font-size: 14px;
        }

        .summary-value {
            font-size: 27px;
            font-weight: 750;
            margin-top: 10px;
        }

        div.stButton > button,
        div.stDownloadButton > button {
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# 2. 共用工具
# ==========================================

def money(value):
    return f"NT$ {value:,.0f}"


def flash(message="已儲存成功！"):
    """操作成功後重新整理，顯示右下角通知。"""
    st.session_state["flash_message"] = message
    st.rerun()


def show_flash():
    """右下角 Toast 通知。"""
    message = st.session_state.pop(
        "flash_message", None
    )

    if message:
        st.toast(
            message,
            icon="✅",
            duration="short",
        )


def metric_card(label, value, color=GREEN):
    st.markdown(
        '<div class="summary-card">'
        f'<div class="summary-label">{escape(label)}</div>'
        f'<div class="summary-value" style="color:{color}">'
        f'{money(value)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ==========================================
# 3. 讀取記帳資料
# ==========================================

def get_data():
    records = load_records()

    columns = [
        "date",
        "type",
        "category",
        "item",
        "amount",
        "month",
        "record_index",
    ]

    if not records:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(records)

    # 保留原始 CSV 索引，避免排序後修改錯誤資料
    df["record_index"] = df.index

    df["date"] = pd.to_datetime(
        df["date"],
        format="%Y-%m-%d",
        errors="raise",
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="raise",
    )

    df["month"] = df["date"].dt.strftime(
        "%Y-%m"
    )

    return df.sort_values(
        "date",
        ascending=False,
        kind="stable",
    ).reset_index(drop=True)


def totals(df):
    income = df.loc[
        df["type"] == "收入", "amount"
    ].sum()

    expense = df.loc[
        df["type"] == "支出", "amount"
    ].sum()

    return income, expense, income - expense


def monthly_data(df):
    if df.empty:
        return pd.DataFrame(
            columns=["收入", "支出", "結餘"]
        )

    result = (
        df.groupby(["month", "type"])["amount"]
        .sum()
        .unstack(fill_value=0)
    )

    for column in ["收入", "支出"]:
        if column not in result.columns:
            result[column] = 0

    result = result[
        ["收入", "支出"]
    ].sort_index()

    result["結餘"] = (
        result["收入"] - result["支出"]
    )

    return result


def record_options(df):
    return {
        int(row["record_index"]): (
            f"{row['date']:%Y-%m-%d} | "
            f"{row['type']} | "
            f"{row['category']} | "
            f"{row['item']} | "
            f"{money(row['amount'])}"
        )
        for _, row in df.iterrows()
    }


# ==========================================
# 4. 財務總覽
# ==========================================


def show_overview(df):
    st.subheader("財務總覽")

    # ======================================
    # 1. 計算收入、支出與結餘
    # ======================================

    income, expense, balance = totals(df)

    c1, c2, c3 = st.columns(3)

    with c1:
        metric_card("總收入", income, GREEN)

    with c2:
        metric_card("總支出", expense, RED)

    with c3:
        metric_card(
            "目前結餘",
            balance,
            GREEN if balance >= 0 else RED,
        )

    st.write("")

    # ======================================
    # 2. 空資料處理
    # ======================================

    if df.empty:
        st.info(
            "目前沒有符合條件的記帳資料，"
            "請先新增收入或支出紀錄。"
        )
        return

    # ======================================
    # 3. 財務狀況提醒
    # ======================================

    if balance < 0:
        st.error(
            f"目前支出高於收入 "
            f"{money(abs(balance))}。"
        )

    elif income > 0:
        savings_rate = balance / income

        st.success(
            f"目前儲蓄率為 "
            f"{savings_rate:.1%}。"
        )

    else:
        st.info("目前沒有收入資料。")

    # ======================================
    # 4. 財務摘要
    # ======================================

    st.divider()

    st.markdown("#### 📊 財務摘要")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "記帳筆數",
            f"{len(df)} 筆",
        )

    with c2:
        st.metric(
            "平均收入",
            money(
                income / max(
                    len(df[df["type"] == "收入"]),
                    1,
                )
            ),
        )

    with c3:
        st.metric(
            "平均支出",
            money(
                expense / max(
                    len(df[df["type"] == "支出"]),
                    1,
                )
            ),
        )

    # ======================================
    # 5. 最近五筆記帳紀錄
    # ======================================

    st.divider()

    st.markdown("#### 📋 最近五筆記帳紀錄")

    recent = df.sort_values(
        "date",
        ascending=False,
        kind="stable",
    ).head(5).copy()

    recent = recent[
        [
            "date",
            "type",
            "category",
            "item",
            "amount",
        ]
    ]

    recent["date"] = recent["date"].dt.strftime(
        "%Y-%m-%d"
    )

    recent.columns = [
        "日期",
        "類型",
        "分類",
        "項目",
        "金額",
    ]

    st.dataframe(
        recent,
        hide_index=True,
        width="stretch",
        column_config={
            "金額": st.column_config.NumberColumn(
                "金額",
                format="NT$ %d",
            ),
        },
    )

    st.caption(
        "此表格顯示目前篩選條件下，"
        "日期最新的五筆記帳紀錄。"
    )


# ==========================================
# 5. 每月分析
# ==========================================

def show_monthly_analysis(df):
    st.subheader("每月收入與支出")

    if df.empty:
        st.info("目前沒有資料。")
        return

    monthly = monthly_data(df)

    positions = list(range(len(monthly)))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.bar(
        [x - width / 2 for x in positions],
        monthly["收入"],
        width,
        label="收入",
        color=GREEN,
    )

    ax.bar(
        [x + width / 2 for x in positions],
        monthly["支出"],
        width,
        label="支出",
        color=RED,
    )

    ax.set_xticks(positions)
    ax.set_xticklabels(monthly.index)
    ax.set_ylabel(
        "金額（NT$）",
        rotation=0,
        labelpad=45,
    )
    ax.legend()
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("每月結餘趨勢")

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(
        positions,
        monthly["結餘"],
        marker="o",
        color=BLUE,
        linewidth=2,
    )

    ax.axhline(
        0,
        color="#94A3B8",
        linestyle="--",
    )

    ax.set_xticks(positions)
    ax.set_xticklabels(monthly.index)
    ax.set_ylabel(
        "結餘（NT$）",
        rotation=0,
        labelpad=45,
    )
    ax.grid(axis="y", alpha=0.2)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.dataframe(
        monthly.reset_index(),
        hide_index=True,
        width="stretch",
    )


# ==========================================
# 6. 儲蓄分析
# ==========================================

def show_savings_analysis(df):
    st.subheader("儲蓄率分析")

    income, expense, balance = totals(df)

    if income <= 0:
        st.info("目前沒有收入，無法計算儲蓄率。")
        return

    rate = balance / income

    c1, c2, c3 = st.columns(3)

    c1.metric("收入", money(income))
    c2.metric("支出", money(expense))
    c3.metric("儲蓄率", f"{rate:.1%}")

    if rate < 0:
        st.error("目前支出高於收入。")
    else:
        st.progress(
            float(min(max(rate, 0), 1))
        )
        st.success(
            f"目前保留 {money(balance)}。"
        )

    st.caption(
        "此儲蓄率根據收入與支出計算，"
        "不等於儲蓄目標中的存款進度。"
    )


# ==========================================
# 7. 支出分析
# ==========================================

def show_expense_analysis(df):
    st.subheader("支出分類分析")

    expenses = df[
        df["type"] == "支出"
    ]

    if expenses.empty:
        st.info("目前沒有支出資料。")
        return

    summary = (
        expenses.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    c1, c2 = st.columns(2)

    with c1:
        fig, ax = plt.subplots(figsize=(6, 4))

        ax.pie(
            summary.values,
            labels=summary.index,
            autopct="%1.1f%%",
            startangle=90,
        )

        ax.axis("equal")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with c2:
        st.dataframe(
            summary.rename(
                "支出金額"
            ).reset_index(),
            hide_index=True,
            width="stretch",
        )

    st.subheader("單筆支出 TOP 5")

    top = expenses.nlargest(
        5, "amount"
    )[
        ["date", "category", "item", "amount"]
    ].copy()

    top["date"] = top["date"].dt.strftime(
        "%Y-%m-%d"
    )

    st.dataframe(
        top,
        hide_index=True,
        width="stretch",
    )


# ==========================================
# 8. 修改記帳視窗
# ==========================================

@st.dialog("修改記帳紀錄")
def edit_record_dialog(record_index, record):
    with st.form(
        f"edit_dialog_{record_index}"
    ):
        new_date = st.date_input(
            "日期",
            value=record["date"].date(),
        )

        new_type = st.selectbox(
            "類型",
            ["支出", "收入"],
            index=(
                0 if record["type"] == "支出" else 1
            ),
        )

        new_category = st.text_input(
            "分類",
            value=str(record["category"]),
        )

        new_item = st.text_input(
            "項目",
            value=str(record["item"]),
        )

        new_amount = st.number_input(
            "金額",
            min_value=1,
            value=int(record["amount"]),
        )

        submitted = st.form_submit_button(
            "儲存修改",
            type="primary",
        )

    if submitted:
        if not new_category.strip() or not new_item.strip():
            st.error("分類與項目不能空白。")
            return

        try:
            update_record(
                record_index,
                {
                    "date": new_date.strftime(
                        "%Y-%m-%d"
                    ),
                    "type": new_type,
                    "category": new_category.strip(),
                    "item": new_item.strip(),
                    "amount": int(new_amount),
                },
            )

            flash("記帳紀錄已儲存！")

        except (
            ValueError,
            OSError,
            IndexError,
        ) as error:
            st.error(f"修改失敗：{error}")


# ==========================================
# 9. 刪除記帳視窗
# ==========================================

@st.dialog("確認刪除記帳紀錄")
def delete_record_dialog(record_index, record):
    st.warning("刪除後無法透過網頁復原。")

    st.write(
        f"{record['date']:%Y-%m-%d} ｜ "
        f"{record['item']} ｜ "
        f"{money(record['amount'])}"
    )

    confirm = st.checkbox(
        "我確認要刪除這筆資料"
    )

    if st.button(
        "確認刪除",
        type="primary",
        disabled=not confirm,
    ):
        try:
            delete_record_from_csv(
                record_index
            )
            flash("記帳紀錄已刪除！")

        except (
            ValueError,
            OSError,
            IndexError,
        ) as error:
            st.error(f"刪除失敗：{error}")


# ==========================================
# 10. 進階記帳明細
# ==========================================

def show_record_management(df):
    st.subheader("進階記帳管理")

    if df.empty:
        st.info("目前沒有記帳紀錄。")
        return

    with st.container(border=True):
        c1, c2 = st.columns([2, 1])

        with c1:
            keyword = st.text_input(
                "關鍵字搜尋",
                placeholder="搜尋日期、分類或項目",
            )

        with c2:
            record_type = st.selectbox(
                "收支類型",
                ["全部", "收入", "支出"],
            )

        categories = st.multiselect(
            "分類篩選",
            sorted(
                df["category"].dropna().unique()
            ),
        )

        use_dates = st.checkbox(
            "啟用日期區間篩選"
        )

        start_date = None
        end_date = None

        if use_dates:
            dates = st.date_input(
                "日期區間",
                value=(
                    df["date"].min().date(),
                    df["date"].max().date(),
                ),
            )

            if len(dates) != 2:
                st.info("請選擇完整的日期區間。")
                return

            start_date, end_date = dates

        use_amounts = st.checkbox(
            "啟用金額範圍篩選"
        )

        min_amount = None
        max_amount = None

        if use_amounts:
            a1, a2 = st.columns(2)

            with a1:
                min_amount = st.number_input(
                    "最低金額",
                    min_value=0,
                    value=0,
                )

            with a2:
                max_amount = st.number_input(
                    "最高金額",
                    min_value=0,
                    value=int(df["amount"].max()),
                )

            if min_amount > max_amount:
                st.error(
                    "最低金額不能大於最高金額。"
                )
                return

        sort_by = st.selectbox(
            "排序方式",
            [
                "日期：新到舊",
                "日期：舊到新",
                "金額：高到低",
                "金額：低到高",
                "分類：A 到 Z",
            ],
        )

    filtered = filter_records(
        df,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        record_type=record_type,
        categories=categories,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by,
    )

    income, expense, balance = totals(filtered)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("筆數", len(filtered))
    c2.metric("收入", money(income))
    c3.metric("支出", money(expense))
    c4.metric("結餘", money(balance))

    if filtered.empty:
        st.info("找不到符合條件的紀錄。")
        return

    table = filtered[
        ["date", "type", "category", "item", "amount"]
    ].copy()

    table["date"] = table["date"].dt.strftime(
        "%Y-%m-%d"
    )

    table.columns = [
        "日期", "類型", "分類", "項目", "金額"
    ]

    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
    )

    st.download_button(
        "📥 匯出篩選結果",
        data=records_to_csv(filtered),
        file_name="filtered_records.csv",
        mime="text/csv",
    )

    st.divider()
    st.markdown("#### 修改或刪除紀錄")

    options = record_options(filtered)

    selected = st.selectbox(
        "選擇紀錄",
        list(options),
        format_func=lambda x: options[x],
        index=None,
        placeholder="請選擇一筆紀錄",
    )

    if selected is None:
        return

    record = filtered.loc[
        filtered["record_index"] == selected
    ].iloc[0].to_dict()

    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "✏️ 修改紀錄",
            width="stretch",
        ):
            edit_record_dialog(
                selected,
                record,
            )

    with c2:
        if st.button(
            "🗑️ 刪除紀錄",
            width="stretch",
        ):
            delete_record_dialog(
                selected,
                record,
            )


# ==========================================
# 11. 預算管理
# ==========================================

def show_budget_management(df):
    st.subheader("每月預算管理")

    try:
        budgets = load_budgets()

    except (ValueError, OSError) as error:
        st.error(f"讀取預算失敗：{error}")
        return

    current_month = date.today().strftime(
        "%Y-%m"
    )

    months = sorted(
        {current_month}
        | set(df["month"].dropna())
        | {
            row["month"]
            for row in budgets
        },
        reverse=True,
    )

    month = st.selectbox(
        "預算月份",
        months,
        key="budget_month",
    )

    expenses = df[
        (df["month"] == month)
        & (df["type"] == "支出")
    ]

    spending = (
        expenses.groupby("category")["amount"]
        .sum()
        .to_dict()
    )

    month_budgets = [
        row
        for row in budgets
        if row["month"] == month
    ]

    categories = sorted(
        set(spending)
        | {
            row["category"]
            for row in month_budgets
        }
    )

    with st.form("budget_form"):
        category = st.selectbox(
            "分類",
            ["自訂分類"] + categories,
        )

        custom_category = st.text_input(
            "自訂分類"
        )

        amount = st.number_input(
            "預算金額",
            min_value=1,
            value=3000,
            step=100,
        )

        submitted = st.form_submit_button(
            "儲存預算",
            type="primary",
        )

    if submitted:
        category_name = (
            custom_category.strip()
            if category == "自訂分類"
            else category
        )

        if not category_name:
            st.error("請輸入分類名稱。")

        else:
            try:
                upsert_budget(
                    month,
                    category_name,
                    int(amount),
                )

                flash("預算已儲存！")

            except (ValueError, OSError) as error:
                st.error(f"儲存失敗：{error}")

    if not month_budgets:
        st.info("本月尚未設定預算。")
        return

    total_budget = sum(
        row["budget"]
        for row in month_budgets
    )

    spent = sum(
        spending.get(row["category"], 0)
        for row in month_budgets
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "預算總額",
        money(total_budget),
    )

    c2.metric(
        "已編列分類支出",
        money(spent),
    )

    c3.metric(
        "剩餘預算",
        money(total_budget - spent),
    )

    for row in month_budgets:
        category = row["category"]
        budget = row["budget"]
        actual = spending.get(category, 0)
        ratio = actual / budget

        with st.container(border=True):
            st.markdown(f"**{category}**")

            st.write(
                f"{money(actual)} / {money(budget)}"
            )

            st.progress(
                float(min(max(ratio, 0), 1))
            )

            st.caption(
                f"使用率 {ratio:.1%}"
            )

            if ratio > 1:
                st.error(
                    f"超支 {money(actual - budget)}"
                )

            elif ratio >= 0.8:
                st.warning(
                    "已使用超過 80% 預算。"
                )

            else:
                st.success(
                    "仍在預算範圍內。"
                )

            if st.button(
                "刪除預算",
                key=(
                    f"budget_delete_"
                    f"{month}_{category}"
                ),
            ):
                try:
                    delete_budget(
                        month,
                        category,
                    )
                    flash("預算已刪除！")

                except (
                    ValueError,
                    OSError,
                ) as error:
                    st.error(
                        f"刪除失敗：{error}"
                    )

    budgeted_categories = {
        row["category"]
        for row in month_budgets
    }

    unbudgeted = sum(
        value
        for category, value in spending.items()
        if category not in budgeted_categories
    )

    if unbudgeted > 0:
        st.warning(
            "未編列預算的支出："
            + money(unbudgeted)
        )


# ==========================================
# 12. 智慧財務分析
# ==========================================

def show_smart_insights(df):
    st.subheader("智慧財務分析")

    months = sorted(
        set(df["month"].dropna())
        | {
            date.today().strftime("%Y-%m")
        },
        reverse=True,
    )

    month = st.selectbox(
        "分析月份",
        months,
        key="insights_month",
    )

    prior = previous_month(month)

    st.caption(
        f"比較期間：{prior} → {month}"
    )

    has_current = bool(
        (df["month"] == month).any()
    )

    has_previous = bool(
        (df["month"] == prior).any()
    )

    if not has_current:
        st.info("本月沒有記帳資料。")
        return

    comparison = compare_months(
        df,
        month,
    )

    st.markdown("#### 月度收支比較")

    columns = st.columns(3)

    for col, (_, row) in zip(
        columns,
        comparison.iterrows(),
    ):
        change = row["增減金額"]
        percent = row["變化率(%)"]

        if not has_previous:
            delta = "上月無紀錄"

        elif pd.isna(percent):
            delta = (
                f"增減 {money(change)}"
            )

        else:
            delta = (
                f"{change:+,.0f} "
                f"({percent:+.1f}%)"
            )

        col.metric(
            row["指標"],
            money(row["本月"]),
            delta=delta,
            delta_color=(
                "inverse"
                if row["指標"] == "支出"
                else "normal"
            ),
        )

    st.markdown("#### 支出分類變化")

    changes = category_comparison(
        df,
        month,
    )

    if changes.empty:
        st.info("沒有支出分類資料。")

    else:
        if not has_previous:
            changes = changes.copy()

            changes["增減金額"] = float("nan")
            changes["變化率(%)"] = float("nan")

        st.dataframe(
            changes,
            hide_index=True,
            width="stretch",
        )

    st.markdown("#### 自動財務提醒")

    try:
        budgets = load_budgets()

    except (ValueError, OSError) as error:
        budgets = []
        st.warning(
            f"預算讀取失敗：{error}"
        )

    messages = build_insights(
        df,
        month,
        budgets,
    )

    for level, message in messages:
        if level == "error":
            st.error(message)

        elif level == "warning":
            st.warning(message)

        elif level == "success":
            st.success(message)

        else:
            st.info(message)

    report = comparison.copy()

    report.insert(
        0,
        "分析月份",
        month,
    )

    if not has_previous:
        report["上月"] = float("nan")
        report["增減金額"] = float("nan")
        report["變化率(%)"] = float("nan")

    st.download_button(
        "📥 匯出月度分析 CSV",
        data=report.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name=f"insights_{month}.csv",
        mime="text/csv",
    )


# ==========================================
# 13. 儲蓄目標：刪除確認視窗
# ==========================================

@st.dialog("確認刪除儲蓄目標")
def confirm_delete_goal(goal):
    st.warning(
        "刪除目標會同時刪除所有相關存款紀錄，"
        "且無法透過網頁復原。"
    )

    st.write(
        f"目標：**{goal['name']}**"
    )

    confirm = st.checkbox(
        "我確認刪除此目標與存款紀錄"
    )

    if st.button(
        "確認刪除",
        type="primary",
        disabled=not confirm,
    ):
        try:
            delete_goal(
                goal["goal_id"]
            )

            flash("儲蓄目標已刪除！")

        except (ValueError, OSError) as error:
            st.error(
                f"刪除失敗：{error}"
            )


@st.dialog("確認刪除存款紀錄")
def confirm_delete_deposit(deposit):
    st.warning(
        "刪除後，儲蓄進度將重新計算。"
    )

    st.write(
        f"日期：{deposit['date']}"
    )

    st.write(
        f"金額：{money(deposit['amount'])}"
    )

    st.write(
        f"備註：{deposit['note'] or '無'}"
    )

    confirm = st.checkbox(
        "我確認刪除這筆存款"
    )

    if st.button(
        "確認刪除",
        type="primary",
        disabled=not confirm,
    ):
        try:
            delete_deposit(
                deposit["deposit_id"]
            )

            flash("存款紀錄已刪除！")

        except (ValueError, OSError) as error:
            st.error(
                f"刪除失敗：{error}"
            )


# ==========================================
# 14. 儲蓄目標：建立
# ==========================================

def show_create_savings_goal():
    with st.expander(
        "➕ 建立新的儲蓄目標"
    ):
        with st.form(
            "create_savings_goal"
        ):
            name = st.text_input(
                "目標名稱",
                placeholder="例如：旅遊基金",
            )

            target_amount = st.number_input(
                "目標金額（NT$）",
                min_value=1,
                value=30000,
                step=1000,
            )

            today = date.today()

            target_date = st.date_input(
                "預計完成日期",
                value=date(
                    today.year + 1,
                    today.month,
                    min(today.day, 28),
                ),
            )

            submitted = st.form_submit_button(
                "建立目標",
                type="primary",
            )

        if submitted:
            try:
                create_goal(
                    name,
                    int(target_amount),
                    target_date,
                )

                flash("儲蓄目標已建立！")

            except (ValueError, OSError) as error:
                st.error(
                    f"建立失敗：{error}"
                )


# ==========================================
# 15. 儲蓄目標：修改
# ==========================================

def show_edit_savings_goal(goal):
    with st.expander(
        "✏️ 修改目標設定"
    ):
        with st.form(
            f"edit_savings_{goal['goal_id']}"
        ):
            name = st.text_input(
                "目標名稱",
                value=goal["name"],
            )

            amount = st.number_input(
                "目標金額（NT$）",
                min_value=1,
                value=int(
                    goal["target_amount"]
                ),
                step=100,
            )

            target_date = st.date_input(
                "預計完成日期",
                value=date.fromisoformat(
                    goal["target_date"]
                ),
            )

            submitted = st.form_submit_button(
                "儲存修改",
                type="primary",
            )

        if submitted:
            try:
                update_goal(
                    goal["goal_id"],
                    name,
                    int(amount),
                    target_date,
                )

                flash("儲蓄目標已儲存！")

            except (ValueError, OSError) as error:
                st.error(
                    f"修改失敗：{error}"
                )


# ==========================================
# 16. 儲蓄目標：新增存款
# ==========================================

def show_add_savings_deposit(goal):
    with st.expander(
        "💵 新增存款"
    ):
        with st.form(
            f"add_deposit_{goal['goal_id']}"
        ):
            deposit_date = st.date_input(
                "存款日期",
                value=date.today(),
            )

            amount = st.number_input(
                "存入金額（NT$）",
                min_value=1,
                value=1000,
                step=100,
            )

            note = st.text_input(
                "備註",
                placeholder="例如：本月固定儲蓄",
            )

            submitted = st.form_submit_button(
                "確認存入",
                type="primary",
            )

        if submitted:
            try:
                add_deposit(
                    goal["goal_id"],
                    deposit_date,
                    int(amount),
                    note,
                )

                flash("存款紀錄已儲存！")

            except (ValueError, OSError) as error:
                st.error(
                    f"存入失敗：{error}"
                )


# ==========================================
# 17. 儲蓄目標：存款歷史
# ==========================================

def show_savings_history(goal, deposits):
    goal_deposits = [
        row
        for row in deposits
        if row["goal_id"] == goal["goal_id"]
    ]

    with st.expander(
        f"📋 存款歷史（{len(goal_deposits)} 筆）"
    ):
        if not goal_deposits:
            st.info("目前沒有存款紀錄。")
            return

        history = pd.DataFrame(
            goal_deposits
        )[
            ["date", "amount", "note"]
        ]

        history.columns = [
            "日期", "金額", "備註"
        ]

        st.dataframe(
            history.sort_values(
                "日期",
                ascending=False,
            ),
            hide_index=True,
            width="stretch",
        )

        options = {
            row["deposit_id"]: (
                f"{row['date']} | "
                f"{money(row['amount'])} | "
                f"{row['note'] or '無備註'}"
            )
            for row in goal_deposits
        }

        selected = st.selectbox(
            "選擇要刪除的存款",
            list(options),
            format_func=lambda x: options[x],
            index=None,
            key=(
                f"deposit_select_"
                f"{goal['goal_id']}"
            ),
        )

        if selected is not None:
            if st.button(
                "刪除這筆存款",
                key=(
                    f"delete_deposit_"
                    f"{goal['goal_id']}"
                ),
            ):
                deposit = next(
                    row
                    for row in goal_deposits
                    if row["deposit_id"] == selected
                )

                confirm_delete_deposit(
                    deposit
                )


# ==========================================
# 18. 儲蓄目標管理
# ==========================================

def show_savings_goals():
    st.subheader("儲蓄目標管理")

    st.caption(
        "建立儲蓄計畫、追蹤進度，"
        "並估算每月需要存下的金額。"
    )

    try:
        goals = load_goals()
        deposits = load_deposits()

    except (ValueError, OSError) as error:
        st.error(
            f"讀取儲蓄資料失敗：{error}"
        )
        return

    show_create_savings_goal()

    if not goals:
        st.info(
            "目前沒有儲蓄目標，"
            "請先建立第一個目標。"
        )
        return

    total_saved = 0
    total_target = 0
    completed_count = 0

    for goal in goals:
        progress = get_goal_progress(
            goal,
            deposits,
        )

        total_saved += progress["saved"]
        total_target += progress["target"]

        if progress["completed"]:
            completed_count += 1

    st.markdown("#### 儲蓄總覽")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "目標數量",
        f"{len(goals)} 個",
    )

    c2.metric(
        "目標總額",
        money(total_target),
    )

    c3.metric(
        "累積存款",
        money(total_saved),
    )

    c4.metric(
        "已完成目標",
        f"{completed_count} 個",
    )

    st.divider()

    for goal in goals:
        progress = get_goal_progress(
            goal,
            deposits,
        )

        saved = progress["saved"]
        target = progress["target"]
        remaining = progress["remaining"]
        ratio = progress["progress"]

        monthly_required = get_monthly_required(
            goal,
            deposits,
        )

        with st.container(border=True):
            header1, header2 = st.columns(
                [3, 1]
            )

            with header1:
                st.markdown(
                    f"### 🎯 {goal['name']}"
                )

                st.caption(
                    "預計完成日期："
                    + goal["target_date"]
                )

            with header2:
                if progress["completed"]:
                    st.success("已完成")
                else:
                    st.info("進行中")

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "已儲蓄",
                money(saved),
            )

            c2.metric(
                "目標金額",
                money(target),
            )

            c3.metric(
                "尚需儲蓄",
                money(remaining),
            )

            st.progress(
                float(min(max(ratio, 0), 1))
            )

            st.caption(
                f"目前完成 {ratio:.1%}"
            )

            if progress["completed"]:
                st.success(
                    "🎉 恭喜！已達成儲蓄目標。"
                )

            elif monthly_required is None:
                st.error(
                    "目標日期已過，"
                    "但尚未達成儲蓄目標。"
                )

            else:
                st.info(
                    "若要在目標日期前完成，"
                    "從本月至截止月份，"
                    "平均每月約需存入 "
                    + money(monthly_required)
                )

            show_add_savings_deposit(goal)

            show_savings_history(
                goal,
                deposits,
            )

            show_edit_savings_goal(goal)

            if st.button(
                "🗑️ 刪除整個儲蓄目標",
                key=(
                    f"delete_goal_"
                    f"{goal['goal_id']}"
                ),
            ):
                confirm_delete_goal(goal)


# ==========================================
# 19. 財務報告中心（第 32 階段）
# ==========================================

def show_financial_report(df):
    st.subheader("財務報告中心")

    st.caption(
        "自動整理每月收支、預算、"
        "儲蓄目標與財務建議，"
        "並下載 PDF 或 Excel 報告。"
    )

    current_month = date.today().strftime(
        "%Y-%m"
    )

    available_months = sorted(
        set(df["month"].dropna().tolist())
        | {current_month},
        reverse=True,
    )

    selected_month = st.selectbox(
        "選擇報告月份",
        available_months,
        key="financial_report_month",
    )

    try:
        budgets = load_budgets()
        goals = load_goals()
        deposits = load_deposits()

        report = build_monthly_report(
            records_df=df,
            month=selected_month,
            budgets=budgets,
            goals=goals,
            deposits=deposits,
        )

    except (
        ValueError,
        OSError,
        KeyError,
    ) as error:
        st.error(
            f"財務報告資料整理失敗：{error}"
        )
        return

    st.divider()

    # ----------------------------------
    # 財務摘要
    # ----------------------------------

    st.markdown("### 一、財務摘要")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "本月收入",
        money(report["income"]),
    )

    c2.metric(
        "本月支出",
        money(report["expense"]),
    )

    c3.metric(
        "本月結餘",
        money(report["balance"]),
    )

    c4, c5 = st.columns(2)

    savings_rate = report["savings_rate"]

    c4.metric(
        "儲蓄率",
        (
            f"{savings_rate:.1f}%"
            if savings_rate is not None
            else "無法計算"
        ),
    )

    c5.metric(
        "記帳筆數",
        f"{report['record_count']} 筆",
    )

    # ----------------------------------
    # 支出分類
    # ----------------------------------

    st.divider()

    st.markdown("### 二、支出分類分析")

    if report["categories"]:
        category_df = pd.DataFrame(
            report["categories"]
        )

        category_df.columns = [
            "分類",
            "支出金額",
            "占比 (%)",
        ]

        st.dataframe(
            category_df,
            hide_index=True,
            width="stretch",
        )

        chart_data = (
            category_df.set_index("分類")[
                ["支出金額"]
            ]
        )


        fig, ax = plt.subplots(figsize=(10, 4))

        ax.bar(
            chart_data.index,
            chart_data["支出金額"],
            color=RED,
            width=0.6,
        )

        # 分類名稱水平顯示
        ax.tick_params(axis="x", labelrotation=0)

        # 確保中文標籤完整顯示
        ax.set_xticks(range(len(chart_data.index)))
        ax.set_xticklabels(
            chart_data.index,
            rotation=0,
            ha="center",
        )

        ax.set_ylabel("")
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)

        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)


    else:
        st.info("本月沒有支出資料。")

    # ----------------------------------
    # 預算執行情況
    # ----------------------------------

    st.divider()

    st.markdown("### 三、預算執行情況")

    if report["budgets"]:
        for row in report["budgets"]:
            with st.container(border=True):
                st.markdown(
                    f"**{row['category']}**"
                )

                st.write(
                    "預算："
                    + money(row["budget"])
                )

                st.write(
                    "已使用："
                    + money(row["spent"])
                )

                st.progress(
                    float(
                        min(
                            max(
                                row["percentage"] / 100,
                                0,
                            ),
                            1,
                        )
                    )
                )

                st.caption(
                    f"使用率："
                    f"{row['percentage']:.1f}%"
                )

                if row["remaining"] < 0:
                    st.error(
                        "超出預算："
                        + money(
                            abs(row["remaining"])
                        )
                    )

                else:
                    st.success(
                        "剩餘預算："
                        + money(row["remaining"])
                    )

    else:
        st.info("本月尚未設定預算。")

    # ----------------------------------
    # 儲蓄目標進度
    # ----------------------------------

    st.divider()

    st.markdown("### 四、儲蓄目標進度")

    if report["savings_goals"]:
        for goal in report["savings_goals"]:
            with st.container(border=True):
                st.markdown(
                    f"**🎯 {goal['name']}**"
                )

                st.write(
                    f"已存：{money(goal['saved'])}"
                    f" / {money(goal['target'])}"
                )

                st.progress(
                    float(
                        min(
                            max(
                                goal["percentage"] / 100,
                                0,
                            ),
                            1,
                        )
                    )
                )

                st.caption(
                    f"完成進度："
                    f"{goal['percentage']:.1f}%"
                    f" ｜ 目標日期："
                    f"{goal['target_date']}"
                )

    else:
        st.info("本月沒有儲蓄目標。")

    # ----------------------------------
    # 智慧財務建議
    # ----------------------------------

    st.divider()

    st.markdown("### 五、智慧財務建議")

    for message in report["insights"]:
        st.info(message)

    # ----------------------------------
    # 本月記帳明細
    # ----------------------------------

    st.divider()

    st.markdown("### 六、本月記帳明細")

    if report["transactions"]:
        transactions_df = pd.DataFrame(
            report["transactions"]
        )

        transactions_df.columns = [
            "日期",
            "類型",
            "分類",
            "項目",
            "金額",
        ]

        st.dataframe(
            transactions_df,
            hide_index=True,
            width="stretch",
        )

    else:
        st.info("本月沒有記帳紀錄。")

    # ----------------------------------
    # PDF / Excel 匯出
    # ----------------------------------

    st.divider()

    st.markdown("### 📥 下載財務報告")

    st.caption(
        "下載內容包含財務摘要、"
        "分類支出、預算、儲蓄目標、"
        "智慧建議與記帳明細。"
    )

    try:
        pdf_bytes = export_pdf(report)
        excel_bytes = export_excel(report)

    except Exception as error:
        st.error(
            f"報告匯出失敗：{error}"
        )
        return

    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            label="📄 下載 PDF 報告",
            data=pdf_bytes,
            file_name=(
                f"finance_report_"
                f"{selected_month}.pdf"
            ),
            mime="application/pdf",
            width="stretch",
            type="primary",
        )

    with c2:
        st.download_button(
            label="📊 下載 Excel 報告",
            data=excel_bytes,
            file_name=(
                f"finance_report_"
                f"{selected_month}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            width="stretch",
        )


# ==========================================
# 20. Dashboard 分頁導覽
# ==========================================

def show_dashboard(df):
    months = sorted(
        df["month"].dropna().unique(),
        reverse=True,
    )

    st.sidebar.markdown("#### 財務篩選")

    month = st.sidebar.selectbox(
        "月份",
        ["全部月份"] + list(months),
    )

    record_type = st.sidebar.selectbox(
        "收支類型",
        ["全部", "收入", "支出"],
    )

    filtered = df.copy()

    if month != "全部月份":
        filtered = filtered[
            filtered["month"] == month
        ]

    if record_type != "全部":
        filtered = filtered[
            filtered["type"] == record_type
        ]

    st.sidebar.caption(
        f"目前顯示 {len(filtered)} 筆資料"
    )

    pages = [
        "總覽",
        "每月分析",
        "儲蓄分析",
        "支出分析",
        "記帳明細",
        "預算管理",
        "智慧分析",
        "儲蓄目標",
        "財務報告",
    ]

    page = st.segmented_control(
        "功能分頁",
        pages,
        default="總覽",
        selection_mode="single",
        label_visibility="collapsed",
        width="stretch",
    )

    st.write("")

    if page == "總覽":
        show_overview(filtered)

    elif page == "每月分析":
        show_monthly_analysis(filtered)

    elif page == "儲蓄分析":
        show_savings_analysis(filtered)

    elif page == "支出分析":
        show_expense_analysis(filtered)

    elif page == "記帳明細":
        show_record_management(df)

    elif page == "預算管理":
        show_budget_management(df)

    elif page == "智慧分析":
        show_smart_insights(df)

    elif page == "儲蓄目標":
        show_savings_goals()

    elif page == "財務報告":
        show_financial_report(df)


# ==========================================
# 21. 新增記帳資料
# ==========================================

def show_add_record():
    st.subheader("新增記帳資料")

    with st.form(
        "add_record_form",
        clear_on_submit=True,
    ):
        record_date = st.date_input(
            "日期",
            value=date.today(),
        )

        record_type = st.selectbox(
            "類型",
            ["支出", "收入"],
        )

        category = st.text_input(
            "分類",
            placeholder="例如：飲食",
        )

        item = st.text_input(
            "項目",
            placeholder="例如：午餐",
        )

        amount = st.number_input(
            "金額",
            min_value=1,
            value=100,
        )

        submitted = st.form_submit_button(
            "新增紀錄",
            type="primary",
        )

    if submitted:
        if not category.strip() or not item.strip():
            st.error(
                "分類與項目不能空白。"
            )
            return

        try:
            add_record_to_csv({
                "date": record_date.strftime(
                    "%Y-%m-%d"
                ),
                "type": record_type,
                "category": category.strip(),
                "item": item.strip(),
                "amount": int(amount),
            })

            flash("記帳資料已儲存！")

        except (ValueError, OSError) as error:
            st.error(
                f"新增失敗：{error}"
            )


# ==========================================
# 22. 左側選單：修改記帳
# ==========================================

def show_edit_record(df):
    st.subheader("修改記帳資料")

    if df.empty:
        st.info("目前沒有紀錄。")
        return

    options = record_options(df)

    selected = st.selectbox(
        "選擇紀錄",
        list(options),
        format_func=lambda x: options[x],
        index=None,
        key="sidebar_edit_record",
    )

    if selected is not None:
        record = df.loc[
            df["record_index"] == selected
        ].iloc[0].to_dict()

        if st.button(
            "開始修改",
            type="primary",
        ):
            edit_record_dialog(
                selected,
                record,
            )


# ==========================================
# 23. 左側選單：刪除記帳
# ==========================================

def show_delete_record(df):
    st.subheader("刪除記帳資料")

    if df.empty:
        st.info("目前沒有紀錄。")
        return

    options = record_options(df)

    selected = st.selectbox(
        "選擇紀錄",
        list(options),
        format_func=lambda x: options[x],
        index=None,
        key="sidebar_delete_record",
    )

    if selected is not None:
        record = df.loc[
            df["record_index"] == selected
        ].iloc[0].to_dict()

        if st.button(
            "刪除紀錄",
            type="primary",
        ):
            delete_record_dialog(
                selected,
                record,
            )


# ==========================================
# 24. 主程式
# ==========================================

def main():
    apply_style()

    st.title("個人財務管理系統")

    st.caption(
        "Personal Finance Dashboard"
    )

    show_flash()

    st.sidebar.title("財務管理")

    page = st.sidebar.radio(
        "選擇功能",
        [
            "財務分析 Dashboard",
            "新增記帳資料",
            "修改記帳資料",
            "刪除記帳資料",
        ],
    )

    st.sidebar.divider()

    if st.sidebar.button(
        "🔄 重新整理資料"
    ):
        st.rerun()

    try:
        df = get_data()

    except (
        ValueError,
        OSError,
        KeyError,
    ) as error:
        st.error(
            f"記帳資料讀取失敗：{error}"
        )
        st.stop()

    if page == "財務分析 Dashboard":
        show_dashboard(df)

    elif page == "新增記帳資料":
        show_add_record()

    elif page == "修改記帳資料":
        show_edit_record(df)

    elif page == "刪除記帳資料":
        show_delete_record(df)


# ==========================================
# 25. 程式進入點
# ==========================================

if __name__ == "__main__":
    main()
