
# 個人記帳分析系統 - 第 19 階段
# 記帳資料查詢功能

from datetime import datetime


# ==============================
# 1. 顯示查詢結果
# ==============================

def show_search_results(records):

    print("\n========== 查詢結果 ==========")

    if not records:
        print("找不到符合條件的記帳資料。")
        return

    for index, record in enumerate(records, start=1):

        print(f"\n第 {index} 筆")
        print("日期：", record["date"])
        print("類型：", record["type"])
        print("分類：", record["category"])
        print("項目：", record["item"])
        print("金額：", record["amount"], "元")
        print("--------------------")

    print(f"\n共找到 {len(records)} 筆資料。")


# ==============================
# 2. 依日期查詢
# ==============================

def search_by_date(records):

    while True:

        date = input(
            "\n請輸入查詢日期 (YYYY-MM-DD，exit 取消)："
        ).strip()

        if date.lower() == "exit":
            return

        try:
            parsed_date = datetime.strptime(
                date, "%Y-%m-%d"
            )

            if parsed_date.strftime("%Y-%m-%d") != date:
                print("日期格式錯誤！")
                continue

            break

        except ValueError:
            print("日期無效！請重新輸入。")

    results = [
        record for record in records
        if record["date"] == date
    ]

    show_search_results(results)


# ==============================
# 3. 依分類查詢
# ==============================

def search_by_category(records):

    while True:

        category = input(
            "\n請輸入分類名稱 (exit 取消)："
        ).strip()

        if category.lower() == "exit":
            return

        if category:
            break

        print("分類不能留空！")

    results = [
        record for record in records
        if record["category"].casefold() == category.casefold()
    ]

    show_search_results(results)


# ==============================
# 4. 依收入或支出查詢
# ==============================

def search_by_type(records):

    while True:

        record_type = input(
            "\n請輸入類型 (收入/支出，exit 取消)："
        ).strip()

        if record_type.lower() == "exit":
            return

        if record_type in ["收入", "支出"]:
            break

        print("只能輸入收入或支出！")

    results = [
        record for record in records
        if record["type"] == record_type
    ]

    show_search_results(results)


# ==============================
# 5. 依月份查詢
# ==============================

def search_by_month(records):

    while True:

        month = input(
            "\n請輸入月份 (YYYY-MM，exit 取消)："
        ).strip()

        if month.lower() == "exit":
            return

        try:
            parsed_month = datetime.strptime(
                month, "%Y-%m"
            )

            if parsed_month.strftime("%Y-%m") != month:
                print("月份格式錯誤！")
                continue

            break

        except ValueError:
            print("月份無效！請重新輸入。")

    results = [
        record for record in records
        if record["date"].startswith(month + "-")
    ]

    show_search_results(results)


# ==============================
# 6. 查詢功能選單
# ==============================

def search_menu(records):

    while True:

        print("\n========== 記帳資料查詢 ==========")
        print("1. 依日期查詢")
        print("2. 依分類查詢")
        print("3. 依收入或支出查詢")
        print("4. 依月份查詢")
        print("5. 返回主選單")

        choice = input(
            "\n請選擇查詢方式 (1-5)："
        ).strip().lower()

        if choice in ["5", "exit"]:
            print("\n返回主選單。")
            break

        elif choice == "1":
            search_by_date(records)

        elif choice == "2":
            search_by_category(records)

        elif choice == "3":
            search_by_type(records)

        elif choice == "4":
            search_by_month(records)

        else:
            print("輸入錯誤！請輸入 1-5。")
