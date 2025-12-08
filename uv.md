# ⚡ uv Python 套件管理工具指南

`uv` 是一個由 Rust 編寫的極速 Python 套件與專案管理工具。它的目標是取代 `pip`、`poetry`、`pyenv` 和 `virtualenv`，提供一站式的開發體驗。

---

## 1. 安裝 (Installation)

**macOS / Linux**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

安裝後驗證：

```bash
uv --version
```

---

## 2. 核心工作流：新專案 (New Project)

這是使用 `uv` 開發新專案（例如 Google ADK）的標準流程。

### 步驟 A：初始化

```bash
mkdir my-project
cd my-project

# 初始化專案 (建立 pyproject.toml, .python-version)
uv init

# (選用) 指定 Python 版本
uv python pin 3.11
```

### 步驟 B：新增套件

這會自動建立虛擬環境 (`.venv`) 並安裝套件。

```bash
# 加入一般套件
uv add google-genai python-dotenv

# 加入開發用套件 (不會打包到正式環境)
uv add --dev pytest ruff
```

### 步驟 C：執行程式

**不需要** 手動 `source .venv/bin/activate`，`uv` 會自動使用環境。

```bash
uv run main.py
```

---

## 3. 既有專案工作流 (Existing Projects)

接手別人的專案或跑舊 Code 時的處理方式。

### 情境 A：只有 `requirements.txt`

#### 方法 1：轉移成 uv 專案 (推薦)

將舊專案現代化，改用 `pyproject.toml` 管理。

```bash
uv init
uv add -r requirements.txt
uv run main.py
```

#### 方法 2：傳統模式 (Legacy)

不改變專案結構，純粹用 uv 加速安裝。

```bash
uv venv                       # 建立虛擬環境
uv pip install -r requirements.txt  # 安裝依賴
uv run main.py
```

### 情境 B：已有 `pyproject.toml`

例如從 GitHub Clone 下來的 Poetry 或 uv 專案。

```bash
# 根據 lock 檔或 toml 檔同步所有環境
uv sync

# 開始執行
uv run main.py
```

### 情境 C：臨時跑單一腳本 (Single Script)

不想建環境，只想跑一個需要依賴的腳本。

```bash
# 自動建立暫時環境，安裝 pandas 後執行，跑完即焚
uv run --with pandas --with requests script.py
```

---

## 4. 進階技巧：PEP 723 (Script with Metadata)

你可以直接將依賴寫在 `.py` 檔案頭部，任何人拿到這個檔案，只要有裝 `uv` 就能直接跑，完全不用手動安裝套件。

**檔案範例 (`agent_demo.py`):**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai",
#     "python-dotenv",
# ]
# ///

import os
from google import genai

# ... 你的程式碼 ...
```

**執行方式:**

```bash
uv run agent_demo.py
```

---

## 5. 工具指令 (Tools)

執行那些「不屬於專案依賴」的工具（如 Linter、Formatter）。

```bash
# 執行 ruff 檢查代碼 (免安裝到專案)
uvx ruff check .

# 執行 http 測試伺服器
uvx pycowsay "Hello World"
```

---

## 6. 指令對照表 (Cheat Sheet)

| 傳統習慣 (pip/venv)               | uv 新習慣                    | 說明                             |
| :-------------------------------- | :--------------------------- | :------------------------------- |
| `python -m venv .venv`            | **(自動)**                   | `uv init` 或 `uv add` 時自動建立 |
| `source .venv/bin/activate`       | **(不需要)**                 | 使用 `uv run` 即可               |
| `pip install requests`            | `uv add requests`            | 加入並鎖定版本                   |
| `pip install -r requirements.txt` | `uv add -r requirements.txt` | 匯入舊依賴                       |
| `pip freeze > requirements.txt`   | `uv export`                  | 匯出依賴清單                     |
| `pyenv local 3.10`                | `uv python pin 3.10`         | 鎖定 Python 版本                 |
| `python script.py`                | `uv run script.py`           | 確保使用正確環境                 |

---

## 🚀 uv 常用指令速查表

### 1. 專案管理 (Project Basics)

最頻繁使用的核心指令。

| 指令               | 說明                                             |
| :----------------- | :----------------------------------------------- |
| `uv init`          | 初始化當前目錄為 uv 專案 (建立 `pyproject.toml`) |
| `uv init <專案名>` | 建立一個新資料夾並初始化專案                     |
| `uv run <檔案.py>` | **最常用**。在專案虛擬環境中執行 Python 檔案     |
| `uv sync`          | 根據 `.lock` 檔同步環境 (確保與隊友環境一致)     |
| `uv lock`          | 更新 `uv.lock` 鎖定檔但不安裝套件                |

---

### 2. 套件增刪 (Dependencies)

用來管理 `pyproject.toml` 中的依賴。

| 指令                    | 說明                                           |
| :---------------------- | :--------------------------------------------- |
| `uv add <套件名>`       | 安裝套件並加入依賴 (例：`uv add numpy`)        |
| `uv add --dev <套件名>` | 安裝**開發用**依賴 (例：`uv add --dev pytest`) |
| `uv remove <套件名>`    | 移除套件並清理依賴                             |
| `uv tree`               | 顯示已安裝套件的依賴樹狀圖 (查衝突好用)        |
| `uv export`             | 將依賴匯出為 `requirements.txt` 格式           |

---

### 3. Python 版本控制 (Python Versions)

uv 會自動幫你下載並管理 Python 版本，不需手動安裝。

| 指令                       | 說明                                                        |
| :------------------------- | :---------------------------------------------------------- |
| `uv python list`           | 列出所有可用的 Python 版本 (包含已安裝與可下載)             |
| `uv python install 3.12`   | 下載並安裝特定版本的 Python                                 |
| `uv python pin 3.10`       | **鎖定**當前專案使用 Python 3.10 (會寫入 `.python-version`) |
| `uv python uninstall 3.11` | 移除特定版本的 Python                                       |

---

### 4. 全域工具與臨時執行 (Tools & Scripts)

用來跑一些不屬於專案依賴的工具 (如 linter, formatter)。

| 指令                          | 說明                                                                   |
| :---------------------------- | :--------------------------------------------------------------------- |
| `uvx <工具名>`                | 臨時下載並執行工具 (跑完即焚) 例：`uvx ruff check .`                   |
| `uv tool install <工具名>`    | 將工具安裝到全域 (類似 `pipx install`) 例：`uv tool install black`     |
| `uv run --with <套件> <檔案>` | 臨時掛載套件來跑腳本 (不污染環境) 例：`uv run --with pandas script.py` |

---

### 5. 傳統 pip 相容模式 (Legacy / Pip)

當你不想用 `uv init` 管理專案，只想把 uv 當成超快的 pip 使用時。

| 指令                                 | 說明                                 |
| :----------------------------------- | :----------------------------------- |
| `uv venv`                            | 建立一個標準的 `.venv` 虛擬環境      |
| `uv pip install -r requirements.txt` | 快速安裝 `requirements.txt` 內的套件 |
| `uv pip install <套件名>`            | 單純安裝套件到環境中                 |
| `uv pip freeze`                      | 列出當前環境的所有套件               |

---

#### 💡 小撒步

- **忘記指令怎麼打？** 加上 `--help`，例如 `uv add --help`。
- **想升級 uv 本身？** 執行 `uv self update`。
- **磁碟空間不足？** 執行 `uv cache clean` 清理下載快取。
