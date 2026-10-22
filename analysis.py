
# 個人記帳分析系統 - 第 14 階段
# 使用 Pandas 進行記帳資料分析

import pandas as pd
from pathlib import Path


# ==============================
# 1. 設定檔案路徑
# ==============================

file_path = Path(__file__).resolve().parent / "data" / "records.csv"


# ==============================
# 2. 讀取 CSV 資料
# ==============================

def load_data():

    # 確認 CSV 是否存在
    if not file_path.exists():
        print("找不到 records.csv！")
        return None

    # 讀取 CSV
    df = pd.read_csv(
        file_path,
        encoding="utf-8-sig"
    )

    return df


# ==============================
# 3. 顯示資料基本資訊
# ==============================

def show_data_info(df):

    print("\n========== 資料基本資訊 ==========")

    # 顯示資料筆數
    print("資料筆數：", len(df))

    # 顯示前五筆資料
    print("\n前五筆資料：")
    print(df.head())

    # 顯示欄位名稱
    print("\n欄位名稱：")
    print(df.columns.tolist())


# ==============================
# 4. 分析各分類支出
# ==============================

def analyze_expenses(df):

    print("\n========== 各分類支出分析 ==========")

    # 篩選支出資料
    expense_df = df[df["type"] == "支出"]

    # 確認是否有支出資料
    if expense_df.empty:
        print("目前沒有支出資料！")
        return

    # 按分類加總支出金額，並由大到小排序
    category_expenses = (
        expense_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    # 顯示各分類支出
    print("\n各分類支出總額：")
    print(category_expenses)

    # 找出最高支出分類
    top_category = category_expenses.idxmax()
    top_amount = category_expenses.max()

    print("\n最高支出分類：", top_category)
    print("最高支出金額：", top_amount, "元")


# ==============================
# 5. 每月收支分析
# ==============================

def analyze_monthly(df):

    print("\n========== 每月收支分析 ==========")

    # 複製 DataFrame，避免修改原始資料
    monthly_df = df.copy()

    # 將日期轉換成 datetime 格式
    monthly_df["date"] = pd.to_datetime(
        monthly_df["date"],
        format="%Y-%m-%d"
    )

    # 擷取年月，例如 2026-09
    monthly_df["month"] = (
        monthly_df["date"].dt.strftime("%Y-%m")
    )

    # 按月份與收支類型分組
    monthly_summary = (
        monthly_df.groupby(["month", "type"])["amount"]
        .sum()
        .unstack(fill_value=0)
    )

    # 確保收入與支出欄位存在
    monthly_summary = monthly_summary.reindex(
        columns=["收入", "支出"],
        fill_value=0
    )

    # 計算每月結餘
    monthly_summary["結餘"] = (
        monthly_summary["收入"]
        - monthly_summary["支出"]
    )

    # 顯示每月統計
    print(monthly_summary)


# ==============================
# 6. 分類支出占比分析
# ==============================

def analyze_expense_percentage(df):

    print("\n========== 分類支出占比 ==========")

    # 篩選支出資料
    expense_df = df[df["type"] == "支出"]

    if expense_df.empty:
        print("目前沒有支出資料！")
        return

    # 計算各分類支出總額
    category_expenses = (
        expense_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    # 計算總支出
    total_expense = category_expenses.sum()

    # 計算每個分類的支出占比
    percentage = (
        category_expenses / total_expense * 100
    )

    # 顯示分類支出占比
    for category, amount in category_expenses.items():

        print(
            f"{category}：{amount} 元，"
            f"占總支出 {percentage[category]:.2f}%"
        )


# ==============================
# 7. 主程式
# ==============================

def main():

    # 讀取 CSV
    df = load_data()

    # 確認是否成功讀取
    if df is None:
        return

    # 確認是否有資料
    if df.empty:
        print("CSV 目前沒有資料！")
        return

    # 顯示基本資訊
    show_data_info(df)

    # 分析各分類支出
    analyze_expenses(df)

    # 分析每月收支
    analyze_monthly(df)

    # 分析分類支出占比
    analyze_expense_percentage(df)


# ==============================
# 8. 程式進入點
# ==============================

if __name__ == "__main__":
    main()
