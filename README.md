# Personal Finance Analysis｜個人財務管理系統

使用 Python 開發的個人財務管理系統，結合 Pandas、Matplotlib 與 Streamlit，提供記帳管理、財務分析及互動式 Dashboard，協助使用者掌握個人收支狀況。

## 主要功能

- **收支紀錄管理**：新增、查詢、修改及刪除記帳資料。
- **財務分析與視覺化**：統計收入、支出、結餘，呈現每月財務趨勢及支出分類圖表。
- **每月預算管理**：設定分類預算，追蹤實際支出與預算差異。
- **儲蓄目標管理**：建立儲蓄目標，記錄存款與達成進度。
- **智慧財務分析**：整理財務數據並提供分析資訊。
- **財務報告匯出**：支援 PDF、Excel 格式。

## 使用技術

- **Python**：主要開發語言
- **Pandas**：資料處理與分析
- **Matplotlib**：資料視覺化
- **Streamlit**：互動式網頁 Dashboard
- **ReportLab / openpyxl**：PDF、Excel 報表匯出
- **CSV**：本機資料儲存

## 專案結構

```text
Personal_Finance_Analysis/
├── dashboard.py          # Streamlit 網頁主程式
├── main.py               # 命令列記帳入口
├── data_manager.py       # 記帳資料讀寫
├── record_manager.py     # 紀錄管理
├── budget_manager.py     # 預算管理
├── savings_manager.py    # 儲蓄目標管理
├── insights.py           # 財務分析與洞察
├── report_manager.py     # 報表資料處理
├── report_exporter.py    # PDF / Excel 匯出
├── analysis.py           # 財務分析
├── visualization.py      # 圖表產生
├── search.py             # 查詢功能
├── project_check.py      # 專案檢查工具
├── data/
│   └── sample_records.csv
├── output/               # 圖表輸出
├── pages/
│   └── __init__.py
├── requirements.txt      # 套件需求
├── .gitignore            # Git 忽略規則
└── README.md             # 專案說明
```

> `.venv/`、`__pycache__/` 與私人財務 CSV 不會包含在公開專案中。

## 安裝與執行

### 1. 建立虛擬環境

```powershell
python -m venv .venv
```

### 2. 啟用虛擬環境

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. 安裝所需套件

```powershell
python -m pip install -r requirements.txt
```

### 4. 初始化範例資料

```powershell
Copy-Item data\sample_records.csv data\records.csv
```

### 5. 啟動 Dashboard

```powershell
python -m streamlit run dashboard.py
```

啟動後開啟瀏覽器：

http://localhost:8501

## 資料安全

個人財務資料儲存在本機 CSV，透過 `.gitignore` 排除私人資料、虛擬環境及快取檔案，避免上傳至 GitHub。

## 專案目的

本專案以實際財務管理需求為基礎，整合 Python 程式設計、資料處理、視覺化與網頁應用開發，作為 Python 學習成果及個人作品集展示。