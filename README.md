# 🚀 網頁自動測試工具

一個採用三層架構設計的網頁自動測試工具，支援隨機點擊測試和元素抓取功能。

## ✨ 特色功能

- 🏗️ **三層架構設計** - 簡潔易維護的分層結構
- 🎯 **簡化 API** - 用戶只需專注測試邏輯
- 🌐 **智能元素抓取** - 自動識別可點擊元素
- 🎲 **隨機點擊測試** - 模擬真實用戶行為
- 📱 **彈性視窗設定** - 可自訂視窗寬度，自動適應螢幕高度
- 🖥️ **有頭/無頭模式** - 支援視覺化和後台運行
- 🔄 **持久瀏覽器會話** - 保持瀏覽器開啟進行連續測試
- 📝 **會話日誌記錄** - 自動記錄每次測試的詳細過程和結果
- 🛑 **循環檢測** - 自動偵測頁面循環，避免無限測試

## 🏗️ 三層架構設計

此項目的核心特色是採用三層架構，讓代碼更加模組化、可維護，並且用戶可以輕易自定義測試流程。

```
┌─────────────────────────────────────────────────────────────┐
│                    第一層：主程式層                           │
│                     main.py                                │
│  🎯 簡單的測試流程，用戶可輕易修改                           │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    第二層：測試引擎層                         │
│                    engine.py                               │
│  🔧 包裝底層功能，提供簡化 API                               │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    第三層：核心功能層                         │
│                    scraper.py                              │
│  ⚙️ 網頁抓取、元素提取、瀏覽器操作                           │
└─────────────────────────────────────────────────────────────┘
```

### 🎯 各層職責

#### 第一層：主程式層 (`main.py`)
- **職責**：測試流程控制、用戶界面、業務邏輯
- **特點**：簡單易懂、用戶可輕易修改
- **主要函數**：
  - `basic_test_flow()` - 基本自動測試流程
  - `interactive_test_flow()` - 互動式測試流程
  - `custom_test_example()` - 自定義測試範例

#### 第二層：測試引擎層 (`engine.py`)
- **職責**：包裝底層功能、提供簡化 API、錯誤處理
- **特點**：中介層、簡化複雜操作、統一接口
- **主要 API**：
  - `get_page_elements(url)` - 獲取頁面元素
  - `click_and_navigate(choice)` - 點擊並導航
  - `start_persistent_browser(url)` - 啟動持久瀏覽器
  - `print_current_elements()` - 顯示當前元素

#### 第三層：核心功能層 (`scraper.py`)
- **職責**：網頁抓取、元素提取、瀏覽器操作
- **特點**：底層實現、功能完整、可重用
- **技術細節**：處理 Selenium、BeautifulSoup 等

### 🎨 架構優勢

1. **關注點分離** - 每層專注於特定職責
2. **易於維護** - 修改一層不影響其他層
3. **用戶友好** - 第一層代碼簡單，隱藏技術細節
4. **可擴展性** - 易於添加新功能和測試策略

## 📦 安裝

1. **安裝依賴項目**：
```bash
pip install -r requirements.txt
```

2. **確保 Chrome 瀏覽器已安裝**
   - 工具會自動下載和管理 ChromeDriver

## 🚀 快速開始

### 快速驗證

```bash
# 首次使用建議先運行快速測試
python test.py
```

### 基本使用

```bash
python main.py
```

選擇測試模式：
1. **基本自動測試** - 隨機點擊測試
2. **互動式測試** - 手動選擇要點擊的元素
3. **自定義測試範例** - 特定類型元素測試

### 自定義測試流程

用戶可以輕鬆修改 `main.py` 中的測試邏輯：

```python
def basic_test_flow():
    # 修改這些設定
    TEST_URL = "https://your-website.com"  # 測試網站
    HEADLESS = False                       # 是否顯示瀏覽器
    MAX_CLICKS = 5                         # 最大點擊次數
    WINDOW_WIDTH = 640                     # 瀏覽器視窗寬度（像素）
    
    engine = TestEngine(headless=HEADLESS, window_width=WINDOW_WIDTH)
    
    if engine.start_persistent_browser(TEST_URL):
        for step in range(MAX_CLICKS):
            # 隨機點擊或指定元素
            element_choice = None  # None=隨機，數字=指定元素
            clicked, new_elements = engine.click_and_navigate(element_choice)
            
            if not clicked:
                break
        
        engine.close_browser()
```

## 💻 使用方法

### API 使用範例

#### 基本使用（第二層 API）

```python
from engine import TestEngine

engine = TestEngine(headless=False, timeout=10, window_width=800)

# 主要方法
engine.start_persistent_browser(url)     # 啟動瀏覽器
engine.print_current_elements()          # 顯示可點擊元素
engine.click_and_navigate(choice)        # 點擊元素並導航
engine.close_browser()                   # 關閉瀏覽器
```

#### 進階使用（直接使用第三層）

```python
from scraper import WebScraper

scraper = WebScraper(use_selenium=True, headless=False, window_width=1024)
elements = scraper.get_clickable_elements_from_url("https://example.com")
```

#### 循環檢測功能

🛑 **重要功能：自動循環檢測**

系統會自動檢測頁面循環，當最新頁面的可點擊元素與之前訪問過的頁面完全相同時，會停止測試並保持瀏覽器視窗開啟。

```python
from engine import TestEngine

engine = TestEngine(headless=False)
engine.start_persistent_browser("https://example.com")

# 執行自動測試（會自動檢測循環）
for step in range(10):
    clicked, new_elements = engine.click_and_navigate()
    
    # 檢查是否檢測到循環
    if engine.is_loop_detected:
        print("🔄 檢測到頁面循環，測試已停止")
        print("🔍 瀏覽器保持開啟供檢查")
        break

# 查看循環檢測狀態
status = engine.get_loop_detection_status()
print(f"已訪問 {status['pages_visited']} 個頁面")
print(f"其中 {status['unique_pages']} 個唯一頁面")

# 控制循環檢測
engine.disable_loop_detection()  # 停用循環檢測
engine.enable_loop_detection()   # 啟用循環檢測
engine.reset_loop_detection()    # 重置檢測狀態
```

**循環檢測特點：**
- 🎯 **智能比較** - 基於頁面元素類型、文字和連結的MD5簽名
- 📊 **歷史追蹤** - 記錄最近20個頁面的簽名避免記憶體問題
- 🔄 **靈活控制** - 可以啟用/停用/重置循環檢測狀態
- 📝 **詳細日誌** - 循環檢測事件會記錄到會話日誌中
- 🔍 **視覺化檢查** - 檢測到循環時保持瀏覽器開啟供觀察

**測試循環檢測功能：**
```bash
python loop_detection_test.py
```

## 📁 項目結構

```
web-auto-test/
├── main.py           # 🎯 第一層：主程式
├── engine.py         # 🔧 第二層：測試引擎
├── scraper.py        # ⚙️ 第三層：網頁抓取器
├── test.py           # 🚀 快速測試
├── requirements.txt  # 📦 依賴項目
├── README.md         # 📚 完整使用說明
└── LICENSE          # 📄 授權文件
```

## 🎮 使用場景

### 1. 基本網站測試
```python
# 在 main.py 中修改
TEST_URL = "https://your-site.com"
HEADLESS = False  # 顯示瀏覽器
MAX_CLICKS = 10   # 測試 10 次點擊
```

### 2. 特定元素測試
```python
def custom_test():
    engine = TestEngine(headless=False)
    if engine.start_persistent_browser("https://example.com"):
        # 只點擊連結類型的元素
        for element in engine.current_elements:
            if element['type'] == 'link':
                engine.click_and_navigate(element['id'])
                break
```

### 3. 批量網站測試
```python
websites = [
    "https://site1.com",
    "https://site2.com", 
    "https://site3.com"
]

engine = TestEngine(headless=True)
for site in websites:
    elements = engine.get_page_elements(site)
    print(f"{site}: {len(elements)} 個可點擊元素")
```

## 📊 輸出範例

```
🎯 開始網頁自動測試
📍 測試網站: https://www.pro360.com.tw
👀 瀏覽器模式: 有頭模式
============================================================

📋 步驟 1: 啟動瀏覽器並分析頁面
🖥️ 檢測到螢幕高度: 932px
📐 設定瀏覽器視窗大小: 640x932
✅ 瀏覽器已啟動，找到 25 個可點擊元素

📋 當前頁面的可點擊元素 (共 25 個):
================================================================================
 1. [LINK  ] 首頁
     🔗 https://www.pro360.com.tw/
 2. [LINK  ] 找專家
     🔗 https://www.pro360.com.tw/search
 3. [BUTTON] 登入
...
```

## 🛠️ 進階設定

### 瀏覽器設定
- **視窗大小**：可自訂寬度（預設 640px）× 全螢幕高度
- **模式**：支援有頭/無頭模式
- **自動管理**：自動下載和配置 ChromeDriver

### 元素識別
- **連結**：`<a>` 標籤
- **按鈕**：`<button>` 和 `<input type="button/submit/reset">`
- **互動元素**：具有 `onclick` 事件的元素

## 📝 會話日誌功能

每次測試會話都會自動生成結構化的 JSON 日誌，專為 LLM 分析而優化，幫助您追蹤測試過程、分析結果和調試問題。

### 🎯 日誌特色

- **LLM 優化** - JSON 格式，專為 AI 分析而設計
- **自動記錄** - 無需額外配置，默認啟用
- **完整追踪** - 記錄每個步驟的時間戳、操作和結果
- **錯誤捕獲** - 詳細記錄失敗原因和錯誤信息
- **性能分析** - 自動計算成功率、平均元素數等關鍵指標
- **結構化數據** - 便於 LLM 解析和分析的標準化格式

### 📁 日誌文件結構

每次測試會話會在 `logs/` 目錄下生成一個 JSON 文件：

```
logs/
└── test_20241220_143052.json    # LLM 分析友好的結構化日誌
```

### 📊 JSON 日誌格式說明

日誌採用結構化 JSON 格式，包含以下主要部分：

```json
{
  "session_id": "test_20241220_143052",
  "start_time": "2024-12-20T14:30:52.123456",
  "end_time": "2024-12-20T14:35:15.789012",
  "config": {
    "headless": false,
    "timeout": 10,
    "window_width": 640,
    "url": "https://www.example.com"
  },
  "steps": [
    {
      "step": 1,
      "timestamp": "2024-12-20T14:30:55.456789",
      "type": "start_browser",
      "details": {
        "url": "https://www.example.com",
        "window_width": 640,
        "initial_elements_count": 8
      },
      "result": "success",
      "error": null
    },
    {
      "step": 2,
      "timestamp": "2024-12-20T14:31:02.123456",
      "type": "click",
      "details": {
        "clicked_element": {
          "type": "link",
          "text": "首頁連結",
          "href": "https://www.example.com/home"
        },
        "new_elements_count": 15,
        "choice_method": "random"
      },
      "result": "success",
      "error": null
    }
  ],
  "errors": [],
  "summary": {
    "total_steps": 8,
    "successful_steps": 7,
    "failed_steps": 1,
    "total_errors": 1,
    "final_elements_count": 12,
    "duration_seconds": 263.08,
    "success_rate": 0.875,
    "avg_elements_per_page": 13.5
  },
  "metadata": {
    "version": "1.0",
    "tool": "web-auto-test",
    "analysis_ready": true,
    "llm_instructions": "This is an automated web testing session log. Analyze patterns, failures, and performance metrics.",
    "key_metrics": [
      "duration_seconds",
      "success_rate",
      "total_errors", 
      "avg_elements_per_page"
    ]
  }
}
```

### ⚙️ 日誌配置

在測試函數中可以控制日誌功能：

```python
def basic_test_flow():
    ENABLE_LOGS = True   # 啟用 LLM 分析日誌 (預設)
    # ENABLE_LOGS = False  # 停用日誌
    
    engine = TestEngine(
        headless=False,
        window_width=640,
        enable_session_log=ENABLE_LOGS  # 傳遞日誌設定
    )
```

### 🤖 LLM 分析建議

將日誌文件發送給 LLM 時，可以要求分析以下方面：

1. **性能評估** - 分析 `success_rate` 和 `duration_seconds`
2. **錯誤模式** - 檢查 `errors` 陣列中的失敗模式
3. **元素豐富度** - 評估 `avg_elements_per_page` 指標
4. **操作流程** - 分析 `steps` 中的點擊路徑和模式
5. **配置優化** - 基於結果建議最佳的 `window_width` 和 `timeout` 設定

### 🔧 日誌管理

```bash
# 查看最新的測試日誌
ls -la logs/ | head -10

# 清理舊日誌文件（保留最近 7 天）
find logs/ -name "*.json" -mtime +7 -delete

# 批量發送給 LLM 分析
cat logs/test_*.json | jq '.'  # 格式化查看
```

## 🔍 疑難排解

### 常見問題

1. **Chrome 瀏覽器未安裝**
   ```
   解決方案：下載並安裝 Google Chrome
   ```

2. **權限問題**
   ```bash
   pip install --user -r requirements.txt
   ```

3. **網路連線問題**
   ```
   檢查網路連線和防火牆設定
   ```

### 調試模式

```python
import logging
logging.basicConfig(level=logging.INFO)

# 然後執行測試
```

## 🔧 開發指南

### 修改測試流程

1. **基本修改**：直接編輯 `main.py` 中的函數
2. **新增測試模式**：在 `main.py` 中添加新的測試函數
3. **修改測試引擎**：在需要新功能時修改 `engine.py`

### 自訂視窗寬度

在各個測試函數中修改 `WINDOW_WIDTH` 變數：

```python
def basic_test_flow():
    WINDOW_WIDTH = 800  # 修改為您想要的寬度
    engine = TestEngine(headless=False, window_width=WINDOW_WIDTH)
    # ... 其他代碼
```

不同場景的建議寬度：
- **手機模擬**：375px 或 414px
- **平板模擬**：768px 或 1024px  
- **桌面標準**：1200px 或 1440px
- **窄屏測試**：640px（預設）

### 自訂日誌功能

控制會話日誌的啟用/停用：

```python
def my_custom_test():
    ENABLE_LOGS = True   # 啟用 LLM 分析日誌
    # ENABLE_LOGS = False  # 停用日誌以提升性能
    
    engine = TestEngine(
        headless=False,
        window_width=800,
        enable_session_log=ENABLE_LOGS
    )
    
    try:
        # 您的測試邏輯
        engine.start_persistent_browser("https://example.com")
        # ... 測試步驟
    finally:
        engine.close_browser()
        
        # 顯示日誌文件路徑
        if ENABLE_LOGS and engine.session_id:
            print(f"📊 LLM 分析日誌: logs/{engine.session_id}.json")
```

**日誌使用場景：**
- **LLM 分析** - 將日誌發送給 AI 進行深度分析
- **開發調試** - 啟用詳細日誌追蹤問題
- **自動化測試** - 記錄測試結果供後續分析
- **性能測試** - 停用日誌減少 I/O 開銷
- **批量測試** - 收集多個會話數據進行比較分析

### 添加新功能

1. **第三層**：在 `scraper.py` 中添加新的底層功能
2. **第二層**：在 `engine.py` 中包裝新功能
3. **第一層**：在 `main.py` 中使用新功能

### 錯誤處理分層

- **第一層**：處理用戶輸入錯誤
- **第二層**：處理業務邏輯錯誤
- **第三層**：處理技術實現錯誤

### 添加新的測試模式
在 `main.py` 中添加新函數：

```python
def my_custom_test():
    engine = TestEngine(headless=False)
    # 你的測試邏輯
    pass

# 在 main() 函數中添加選項
```

### 自定義元素過濾
修改 `engine.py` 中的 `_simplify_elements` 方法。

### 新增瀏覽器支援  
修改 `scraper.py` 中的 `_setup_driver` 方法。

## 📈 擴展性

## 📄 授權

MIT License - 詳見 [LICENSE](LICENSE) 文件

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📞 支援

如果遇到問題，請查看：
1. 上述疑難排解章節
2. GitHub Issues
3. 代碼中的註釋和文檔字符串

---

💡 **提示**: 修改測試流程只需編輯 `main.py`，無需了解底層實現細節！
