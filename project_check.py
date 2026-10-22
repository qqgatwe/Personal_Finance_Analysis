
from pathlib import Path
import ast

BASE_DIR = Path(__file__).resolve().parent

REQUIRED_FILES = [
    "dashboard.py",
    "data_manager.py",
    "budget_manager.py",
    "record_manager.py",
    "savings_manager.py",
    "insights.py",
    "report_manager.py",
    "report_exporter.py",
]

DATA_FILES = [
    "records.csv",
    "budgets.csv",
    "savings_goals.csv",
    "savings_deposits.csv",
]


def check_files():
    print("\n=== 專案檔案檢查 ===")

    for filename in REQUIRED_FILES:
        path = BASE_DIR / filename

        if path.exists():
            print(f"[OK] {filename}")
        else:
            print(f"[缺少] {filename}")


def check_data():
    print("\n=== 資料檔案檢查 ===")

    data_dir = BASE_DIR / "data"

    for filename in DATA_FILES:
        path = data_dir / filename

        if path.exists():
            print(f"[OK] {filename}")
        else:
            print(f"[缺少] {filename}")


def check_python_syntax():
    print("\n=== Python 語法檢查 ===")

    for filename in REQUIRED_FILES:
        path = BASE_DIR / filename

        if not path.exists():
            continue

        try:
            source = path.read_text(
                encoding="utf-8-sig"
            )

            ast.parse(
                source,
                filename=str(path),
            )

            print(f"[PASS] {filename}")

        except (SyntaxError, UnicodeError) as error:
            print(f"[FAIL] {filename}: {error}")


def check_dashboard_size():
    print("\n=== Dashboard 程式碼分析 ===")

    path = BASE_DIR / "dashboard.py"

    if not path.exists():
        return

    source = path.read_text(
        encoding="utf-8-sig"
    )

    lines = source.splitlines()
    tree = ast.parse(source)

    functions = [
        node
        for node in tree.body
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    ]

    print(f"總行數：{len(lines)}")
    print(f"函式數量：{len(functions)}")

    print("\n行數最多的 10 個函式：")

    ranked = sorted(
        functions,
        key=lambda node: (
            node.end_lineno - node.lineno + 1
        ),
        reverse=True,
    )

    for node in ranked[:10]:
        length = (
            node.end_lineno - node.lineno + 1
        )

        print(
            f"{node.name}: {length} 行"
        )


def main():
    print("=" * 45)
    print("Personal Finance Analysis")
    print("Project Structure Check")
    print("=" * 45)

    check_files()
    check_data()
    check_python_syntax()
    check_dashboard_size()

    print("\n檢查完成。")


if __name__ == "__main__":
    main()
