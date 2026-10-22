# 個人記帳分析系統 - 第 21 階段
# 整合 CSV、Pandas、Matplotlib、查詢與資料管理
# 資料處理模組化版本

from data_manager import (
    load_records,
    add_record_to_csv,
    validate_date
)

# 匯入查詢功能
from search import search_menu

# 匯入修改與刪除功能
from record_manager import record_manager_menu

# 匯入 Pandas 分析功能
from analysis import (
    load_data,
    analyze_expenses,
    analyze_monthly,
    analyze_expense_percentage
)

# 匯入 Matplotlib 視覺化功能
from visualization import (
    load_data as load_visualization_data,
    get_monthly_summary,
    plot_monthly_income_expense,
    plot_expense_category,
    plot_monthly_balance,
    OUTPUT_DIR
)


# ==============================
# 1. 顯示所有記帳資料
# ==============================

def show_records(records):

    print("\n========== 記帳明細 ==========")

    if not records:
        print("目前沒有記帳資料！")
        return

    for index, record in enumerate(
        records,
        start=1
    ):

        print(f"\n第 {index} 筆")
        print("日期：", record["date"])
        print("類型：", record["type"])
        print("分類：", record["category"])
        print("項目：", record["item"])
        print("金額：", record["amount"], "元")
        print("--------------------")

    print(
        f"\n目前共有 {len(records)} 筆記帳資料。"
    )


# ==============================
# 2. 計算收入與支出
# ==============================

def calculate_summary(records):

    total_income = 0
    total_expense = 0

    for record in records:

        if record["type"] == "收入":
            total_income += record["amount"]

        elif record["type"] == "支出":
            total_expense += record["amount"]

    balance = total_income - total_expense

    print("\n========== 記帳統計 ==========")
    print("總收入：", total_income, "元")
    print("總支出：", total_expense, "元")
    print("目前結餘：", balance, "元")


# ==============================
# 3. 新增記帳資料
# ==============================

def add_record():

    print("\n========== 新增記帳資料 ==========")
    print("提示：任何步驟輸入 exit 都可以取消新增。")

    # ------------------------------
    # 1. 輸入日期
    # ------------------------------
    while True:

        date = input(
            "\n請輸入日期 (YYYY-MM-DD)："
        ).strip()

        if date.lower() == "exit":
            print("\n已取消新增記帳資料。")
            return

        if validate_date(date):
            break

        print(
            "日期無效！"
            "請輸入正確日期，例如：2026-10-13"
        )

    # ------------------------------
    # 2. 輸入類型
    # ------------------------------
    while True:

        record_type = input(
            "\n請輸入類型 (收入/支出)："
        ).strip()

        if record_type.lower() == "exit":
            print("\n已取消新增記帳資料。")
            return

        if record_type in ["收入", "支出"]:
            break

        print(
            "類型錯誤！"
            "只能輸入收入或支出。"
        )

    # ------------------------------
    # 3. 輸入分類
    # ------------------------------
    while True:

        category = input(
            "\n請輸入分類："
        ).strip()

        if category.lower() == "exit":
            print("\n已取消新增記帳資料。")
            return

        if category:
            break

        print("分類不能留空！")


    # ------------------------------
    # 4. 輸入項目
    # ------------------------------
    while True:

        item = input(
            "\n請輸入項目："
        ).strip()

        if item.lower() == "exit":
            print("\n已取消新增記帳資料。")
            return

        if item:
            break

        print("項目不能留空！")


    # ------------------------------
    # 5. 輸入金額
    # ------------------------------
    while True:

        amount_input = input(
            "\n請輸入金額："
        ).strip()

        if amount_input.lower() == "exit":
            print("\n已取消新增記帳資料。")
            return

        try:
            amount = int(amount_input)

            if amount <= 0:
                print("金額必須大於 0！")
                continue

            break

        except ValueError:
            print(
                "金額格式錯誤！"
                "請輸入正整數，例如：150"
            )

    # ------------------------------
    # 6. 建立記帳資料
    # ------------------------------
    record = {
        "date": date,
        "type": record_type,
        "category": category,
        "item": item,
        "amount": amount
    }

    # ------------------------------
    # 7. 顯示確認資料
    # ------------------------------
    print("\n========== 確認記帳資料 ==========")

    print("日期：", record["date"])
    print("類型：", record["type"])
    print("分類：", record["category"])
    print("項目：", record["item"])
    print("金額：", record["amount"], "元")

    # ------------------------------
    # 8. 確認儲存
    # ------------------------------
    while True:

        confirm = input(
            "\n確認儲存？(Y/N，或 exit 取消)："
        ).strip().lower()

        if confirm == "y":

            try:
                add_record_to_csv(record)

                print(
                    "\n新增記帳資料成功！"
                )

            except (OSError, ValueError) as error:
                print(
                    "\n儲存失敗：",
                    error
                )

            return

        elif confirm in ["n", "exit"]:

            print(
                "\n已取消新增記帳資料，"
                "沒有儲存。"
            )
            return

        else:
            print(
                "輸入錯誤！"
                "請輸入 Y、N 或 exit。"
            )


# ==============================
# 4. 執行 Pandas 分析
# ==============================

def run_analysis(choice):

    df = load_data()

    if df is None:
        return

    if df.empty:
        print("目前沒有資料可以分析！")
        return

    if choice == "4":
        analyze_expenses(df)

    elif choice == "5":
        analyze_monthly(df)

    elif choice == "6":
        analyze_expense_percentage(df)


# ==============================
# 5. 產生財務分析圖表
# ==============================

def generate_charts():

    print("\n========== 產生財務分析圖表 ==========")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df = load_visualization_data()

    if df is None:
        return

    if df.empty:
        print("目前沒有資料可以產生圖表！")
        return

    monthly_summary = get_monthly_summary(df)

    # 每月收入與支出
    plot_monthly_income_expense(
        monthly_summary
    )

    # 支出分類占比
    plot_expense_category(df)

    # 每月結餘
    plot_monthly_balance(
        monthly_summary
    )

    print("\n財務分析圖表產生完成！")


# ==============================
# 6. 互動式主選單
# ==============================

def main():

    while True:

        print(
            "\n========== 個人記帳分析系統 =========="
        )

        print("1. 新增記帳資料")
        print("2. 查看所有記帳明細")
        print("3. 查看收入與支出統計")
        print("4. 查看各分類支出分析")
        print("5. 查看每月收支分析")
        print("6. 查看支出分類占比")
        print("7. 產生財務分析圖表")
        print("8. 查詢記帳資料")
        print("9. 管理記帳資料（修改／刪除）")
        print("10. 離開程式")

        choice = input(
            "\n請選擇功能 (1-10，或 exit 離開)："
        ).strip().lower()

        # ------------------------------
        # 1. 新增記帳資料
        # ------------------------------
        if choice == "1":
            add_record()

        # ------------------------------
        # 2. 查看所有記帳資料
        # ------------------------------
        elif choice == "2":

            try:
                records = load_records()
                show_records(records)

            except (OSError, ValueError) as error:
                print(
                    "\n讀取資料失敗：",
                    error
                )

        # ------------------------------
        # 3. 查看收入與支出統計
        # ------------------------------
        elif choice == "3":

            try:
                records = load_records()
                calculate_summary(records)

            except (OSError, ValueError) as error:
                print(
                    "\n讀取資料失敗：",
                    error
                )

        # ------------------------------
        # 4-6. Pandas 分析
        # ------------------------------
        elif choice in ["4", "5", "6"]:
            run_analysis(choice)

        # ------------------------------
        # 7. Matplotlib 圖表
        # ------------------------------
        elif choice == "7":
            generate_charts()

        # ------------------------------
        # 8. 查詢記帳資料
        # ------------------------------
        elif choice == "8":

            try:
                records = load_records()
                search_menu(records)

            except (OSError, ValueError) as error:
                print(
                    "\n讀取資料失敗：",
                    error
                )

        # ------------------------------
        # 9. 修改與刪除
        # ------------------------------
        elif choice == "9":

            record_manager_menu()

        # ------------------------------
        # 10. 離開程式
        # ------------------------------
        elif choice in ["10", "exit"]:

            print(
                "\n感謝使用個人記帳分析系統！"
            )
            break

        # ------------------------------
        # 輸入錯誤
        # ------------------------------
        else:
            print(
                "\n輸入錯誤！"
                "請輸入 1-10 或 exit。"
            )


# ==============================
# 7. 程式進入點
# ==============================

if __name__ == "__main__":
    main()
