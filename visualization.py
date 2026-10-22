
# ==========================================
# 個人記帳分析系統 - 第 24 階段
# Matplotlib 資料視覺化
# 跨電腦相容性與錯誤處理優化版
# ==========================================

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager


# ==========================================
# 1. 設定檔案與輸出路徑
# ==========================================

# 自動取得 visualization.py 所在資料夾
BASE_DIR = Path(__file__).resolve().parent

# CSV 記帳資料路徑
FILE_PATH = BASE_DIR / "data" / "records.csv"

# 圖表輸出資料夾
OUTPUT_DIR = BASE_DIR / "output"


# ==========================================
# 2. 設定中文字型
# ==========================================

def setup_chinese_font():

    # 取得目前電腦已安裝的字型
    available_fonts = {
        font.name
        for font in font_manager.fontManager.ttflist
    }

    # Windows、macOS、Linux 常見中文字型
    font_candidates = [
        "Microsoft JhengHei",
        "Microsoft YaHei",
        "Noto Sans CJK TC",
        "Noto Sans CJK JP",
        "PingFang TC",
        "Heiti TC",
        "SimHei"
    ]

    # 尋找第一個可用的中文字型
    selected_font = next(
        (
            font_name
            for font_name in font_candidates
            if font_name in available_fonts
        ),
        None
    )

    if selected_font:

        plt.rcParams["font.sans-serif"] = [
            selected_font
        ]

        print(
            f"目前使用中文字型：{selected_font}"
        )

    else:

        print(
            "提醒：找不到支援中文的字型，"
            "圖表中文字可能顯示異常。"
        )

    # 避免負數的減號顯示異常
    plt.rcParams["axes.unicode_minus"] = False


# ==========================================
# 3. 讀取 CSV 記帳資料
# ==========================================

def load_data():

    # 檢查 CSV 是否存在
    if not FILE_PATH.exists():

        print(
            "找不到 records.csv！"
        )

        print(
            f"預期路徑：{FILE_PATH}"
        )

        return None

    # 檢查 CSV 是否完全空白
    if FILE_PATH.stat().st_size == 0:

        print(
            "records.csv 是空檔案！"
        )

        return None

    try:

        # 讀取 CSV
        df = pd.read_csv(
            FILE_PATH,
            encoding="utf-8-sig"
        )

    except pd.errors.EmptyDataError:

        print(
            "CSV 沒有可讀取的資料！"
        )

        return None

    # 確認是否有記帳資料
    if df.empty:

        print(
            "目前沒有記帳資料！"
        )

        return None

    # 確認必要欄位存在
    required_columns = [
        "date",
        "type",
        "category",
        "item",
        "amount"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        print(
            "CSV 缺少必要欄位：",
            missing_columns
        )

        return None

    try:

        # 日期轉換
        df["date"] = pd.to_datetime(
            df["date"],
            format="%Y-%m-%d",
            errors="raise"
        )

        # 金額轉換
        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="raise"
        )

    except (ValueError, TypeError) as error:

        print(
            "CSV 資料格式錯誤：",
            error
        )

        return None

    return df


# ==========================================
# 4. 建立每月收支統計
# ==========================================

def get_monthly_summary(df):

    # 複製資料，避免修改原始 DataFrame
    monthly_df = df.copy()

    # 取得年月，例如 2026-09
    monthly_df["month"] = (
        monthly_df["date"]
        .dt.strftime("%Y-%m")
    )

    # 按月份與收支類型加總
    monthly_summary = (
        monthly_df.groupby(
            ["month", "type"]
        )["amount"]
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

    # 依月份排序
    monthly_summary = (
        monthly_summary.sort_index()
    )

    return monthly_summary


# ==========================================
# 5. 每月收入與支出長條圖
# ==========================================

def plot_monthly_income_expense(monthly_summary):

    if monthly_summary.empty:

        print(
            "沒有每月收支資料，略過長條圖。"
        )

        return

    # 確保輸出資料夾存在
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 建立長條圖
    ax = monthly_summary[
        ["收入", "支出"]
    ].plot(
        kind="bar",
        figsize=(10, 6),
        color=["seagreen", "indianred"]
    )

    # 設定標題與座標軸
    ax.set_title("每月收入與支出")
    ax.set_xlabel("月份")
    ax.set_ylabel("金額（元）")

    # 設定 X 軸文字角度
    plt.xticks(rotation=0)

    # 顯示每個長條的金額
    for container in ax.containers:

        ax.bar_label(
            container,
            fmt="%.0f",
            padding=3
        )

    # 避免數字被裁切
    ax.margins(y=0.15)

    # 自動調整排版
    plt.tight_layout()

    # 設定輸出檔案
    output_path = (
        OUTPUT_DIR
        / "monthly_income_expense.png"
    )

    # 儲存圖片
    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    # 關閉圖表
    plt.close()

    print(
        "已儲存：",
        output_path
    )


# ==========================================
# 6. 支出分類占比圓餅圖
# ==========================================

def plot_expense_category(df):

    # 篩選支出資料
    expense_df = df[
        df["type"] == "支出"
    ]

    if expense_df.empty:

        print(
            "沒有支出資料，略過圓餅圖。"
        )

        return

    # 計算各分類支出總額
    category_expenses = (
        expense_df.groupby(
            "category"
        )["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    # 避免總支出為 0
    if category_expenses.sum() <= 0:

        print(
            "支出總額為 0，略過圓餅圖。"
        )

        return

    # 確保輸出資料夾存在
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 建立圖表
    fig, ax = plt.subplots(
        figsize=(8, 8)
    )

    # 繪製圓餅圖
    ax.pie(
        category_expenses.values,
        labels=category_expenses.index,
        autopct="%1.1f%%",
        startangle=90
    )

    # 設定標題
    ax.set_title(
        "支出分類占比"
    )

    # 保持圓形比例
    ax.axis("equal")

    # 自動調整排版
    fig.tight_layout()

    # 設定輸出檔案
    output_path = (
        OUTPUT_DIR
        / "expense_category_pie.png"
    )

    # 儲存圖片
    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    # 關閉圖表
    plt.close(fig)

    print(
        "已儲存：",
        output_path
    )


# ==========================================
# 7. 每月結餘長條圖
# ==========================================

def plot_monthly_balance(monthly_summary):

    if monthly_summary.empty:

        print(
            "沒有每月結餘資料，略過圖表。"
        )

        return

    # 確保輸出資料夾存在
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 取得月份與結餘
    months = monthly_summary.index

    balances = monthly_summary["結餘"]

    # 正數綠色、負數紅色
    colors = [
        "seagreen" if value >= 0
        else "indianred"
        for value in balances
    ]

    # 建立圖表
    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    # 繪製長條圖
    bars = ax.bar(
        months,
        balances,
        color=colors,
        width=0.5
    )

    # 顯示每個月份的結餘金額
    ax.bar_label(
        bars,
        fmt="%.0f",
        padding=4
    )

    # 加入 0 元參考線
    ax.axhline(
        y=0,
        color="gray",
        linestyle="--",
        linewidth=1
    )

    # 設定標題與座標軸
    ax.set_title(
        "每月收支結餘比較"
    )

    ax.set_xlabel("月份")

    ax.set_ylabel("結餘（元）")

    # 避免金額被裁切
    ax.margins(y=0.15)

    # 自動調整排版
    fig.tight_layout()

    # 設定輸出檔案
    output_path = (
        OUTPUT_DIR
        / "monthly_balance.png"
    )

    # 儲存圖片
    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    # 關閉圖表
    plt.close(fig)

    print(
        "已儲存：",
        output_path
    )


# ==========================================
# 8. 主程式
# ==========================================

def main():

    print(
        "\n========== 記帳資料視覺化 =========="
    )

    # 設定中文字型
    setup_chinese_font()

    # 建立 output 資料夾
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 讀取 CSV
    df = load_data()

    if df is None:
        return

    # 建立每月收支統計
    monthly_summary = (
        get_monthly_summary(df)
    )

    # 產生每月收支長條圖
    plot_monthly_income_expense(
        monthly_summary
    )

    # 產生支出分類圓餅圖
    plot_expense_category(df)

    # 產生每月結餘長條圖
    plot_monthly_balance(
        monthly_summary
    )

    print(
        "\n三張財務分析圖表處理完成！"
    )


# ==========================================
# 9. 程式進入點
# ==========================================

# 匯入時也設定中文字型，
# 讓 main.py 呼叫圖表函式時正常顯示中文。
setup_chinese_font()

if __name__ == "__main__":
    main()
