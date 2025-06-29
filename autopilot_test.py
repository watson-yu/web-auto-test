#!/usr/bin/env python3
"""
智能自動駕駛測試程式
基於邏輯優先順序自動導航網站，專門處理表單和對話框
"""

import os
import sys
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 創建logs目錄（如果不存在）
os.makedirs('logs', exist_ok=True)

# 設置日誌配置 - 同時輸出到控制台和文件
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 清除舊的處理器
logger.handlers.clear()

# 創建formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 控制台處理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 文件處理器 - 使用時間戳命名
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = f'logs/autopilot_test_{timestamp}.log'
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info(f"📝 日誌將保存到: {log_filename}")

class AutoPilotTester:
    def __init__(self):
        self.driver = None
        self.max_clicks = 100  # 大幅增加最大點擊次數，看看能走多遠
        self.current_step = 0
        self.test_log = []
        
        # 🛑 循環檢測相關變數
        self.clicked_elements_history = []  # 記錄點擊過的元素
        self.page_states_history = []       # 記錄頁面狀態
        self.is_loop_detected = False       # 是否檢測到循環
        
        self.setup_driver()
    
    def setup_driver(self):
        """設定瀏覽器驅動"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            # 設定視窗大小
            window_width = int(os.getenv('WINDOW_WIDTH', 640))
            chrome_options.add_argument(f"--window-size={window_width},1000")
            
            # 檢查是否使用無頭模式
            headless = os.getenv('HEADLESS_MODE', 'False').lower() == 'true'
            if headless:
                chrome_options.add_argument("--headless")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info("✅ 瀏覽器已啟動")
            
        except Exception as e:
            logger.error(f"啟動瀏覽器失敗: {e}")
            sys.exit(1)
    
    def log_step(self, action, target, result):
        """記錄測試步驟"""
        step_info = {
            'step': self.current_step,
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'target': target,
            'result': result
        }
        self.test_log.append(step_info)
        logger.info(f"步驟 {self.current_step}: {action} -> {target} -> {result}")
    
    def start_autopilot(self, start_url: str):
        """開始自動駕駛測試"""
        try:
            logger.info(f"🚀 開始自動駕駛測試")
            logger.info(f"🌐 起始 URL: {start_url}")
            logger.info(f"🎯 最大點擊次數: {self.max_clicks}")
            
            # 載入起始頁面
            self.driver.get(start_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            
            self.log_step("載入頁面", start_url, "成功")
            
            # 開始自動導航循環
            for step in range(self.max_clicks):
                self.current_step = step + 1
                logger.info(f"\n{'='*60}")
                logger.info(f"🎯 執行步驟 {self.current_step}/{self.max_clicks}")
                
                # 檢測當前頁面狀態
                context = self.analyze_current_context()
                
                # 🛑 檢測循環（在執行動作之前）
                if self.detect_loop():
                    logger.warning("🔄 檢測到循環，停止自動駕駛測試")
                    self.log_step("循環檢測", "重複動作", "檢測到循環")
                    break
                
                # 根據決策邏輯執行動作
                action_result = self.execute_decision_logic(context)
                
                if not action_result:
                    logger.info("❌ 沒有更多可執行的動作，停止自動駕駛")
                    break
                
                # 短暫等待頁面穩定
                time.sleep(2)
            
            logger.info(f"\n🎉 自動駕駛測試完成！總共執行了 {self.current_step} 個步驟")
            self.generate_report()
            
        except Exception as e:
            logger.error(f"自動駕駛測試過程中發生錯誤: {e}")
            self.log_step("錯誤", str(e), "失敗")
        finally:
            self.wait_and_close()
    
    def analyze_current_context(self):
        """分析當前頁面上下文"""
        context = {
            'popup': None,
            'next_buttons': [],
            'disabled_next_buttons': [],
            'input_fields': [],
            'green_buttons': [],
            'all_clickable': []
        }
        
        try:
            # 檢測彈出對話框
            context['popup'] = self.detect_popup()
            search_area = context['popup'] if context['popup'] else self.driver
            
            if context['popup']:
                logger.info("🎯 檢測到彈出對話框，在對話框內搜尋元素")
            else:
                logger.info("📄 在主頁面搜尋元素")
            
            # 查找 "next" 或 "下一步" 按鈕
            next_selectors = [
                "button, input[type='button'], input[type='submit'], [role='button']"
            ]
            
            for selector in next_selectors:
                elements = search_area.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        text = self.get_element_text(element).lower()
                        if 'next' in text or '下一步' in text or '繼續' in text or 'continue' in text:
                            if element.is_enabled() and not self.is_element_disabled(element):
                                context['next_buttons'].append(element)
                                logger.info(f"✅ 找到可點擊的下一步按鈕: '{text}'")
                            else:
                                context['disabled_next_buttons'].append(element)
                                logger.info(f"⚠️  找到禁用的下一步按鈕: '{text}'")
            
            # 查找輸入欄位（單選按鈕、核取方塊等）
            input_selectors = [
                "input[type='radio']",
                "input[type='checkbox']",
                "input[type='text']",
                "input[type='email']",    # 🆕 添加email欄位檢測
                "input[type='password']", # 🆕 添加密碼欄位檢測
                "input[type='date']",     # 🆕 添加日期欄位檢測
                "input[type='tel']",      # 電話號碼欄位
                "input[type='number']",   # 數字欄位
                "select"
            ]
            
            # 🆕 詳細調試：檢查所有找到的元素
            total_found = 0
            total_visible = 0
            total_enabled = 0
            checkbox_debug_info = []
            
            for selector in input_selectors:
                elements = search_area.find_elements(By.CSS_SELECTOR, selector)
                total_found += len(elements)
                
                for element in elements:
                    element_type = element.get_attribute('type')
                    element_name = element.get_attribute('name') or 'none'
                    is_displayed = element.is_displayed()
                    is_enabled = element.is_enabled()
                    
                    if element_type == 'checkbox':
                        # 🆕 對於checkbox，只檢查enabled，不檢查displayed（因為現代網頁設計常隱藏原生checkbox）
                        checkbox_passed = is_enabled
                        checkbox_debug_info.append({
                            'name': element_name,
                            'displayed': is_displayed,
                            'enabled': is_enabled,
                            'passed_filter': checkbox_passed
                        })
                        
                        if checkbox_passed:
                            context['input_fields'].append(element)
                            logger.info(f"☑️  找到有效checkbox: name='{element_name}', value='{element.get_attribute('value') or 'none'}'")
                            total_enabled += 1
                        
                        # 對於checkbox，不需要再經過下面的一般檢查
                        continue
                    
                    if is_displayed:
                        total_visible += 1
                        if is_enabled:
                            total_enabled += 1
                            context['input_fields'].append(element)
            
            # 詳細的調試報告
            logger.info(f"🔍 元素檢測報告: 總共找到 {total_found} 個元素, {total_visible} 個可見, {total_enabled} 個可用")
            
            if checkbox_debug_info:
                logger.info(f"☑️  Checkbox詳細分析:")
                for i, info in enumerate(checkbox_debug_info):
                    logger.info(f"   Checkbox {i+1}: name='{info['name']}', displayed={info['displayed']}, enabled={info['enabled']}, passed={info['passed_filter']}")
            else:
                logger.info(f"☑️  沒有找到任何checkbox元素")
            
            # 🆕 查找城市/地區選擇元素（特殊處理 Pro360 地區選擇）
            area_selection_selectors = [
                ".division-item",  # Pro360 地區選擇項目
                ".area-picker a",  # 地區選擇器中的連結
                "[data-area]",     # 有地區資料屬性的元素
                ".city-option",    # 城市選項
                ".region-item"     # 地區項目
            ]
            
            area_elements = []
            for selector in area_selection_selectors:
                elements = search_area.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        # 檢查是否包含城市名稱
                        text = self.get_element_text(element)
                        if text and len(text) <= 10 and ('市' in text or '縣' in text or '區' in text):
                            area_elements.append(element)
                            context['input_fields'].append(element)  # 也加入輸入欄位列表
            
            if area_elements:
                logger.info(f"🏙️  找到 {len(area_elements)} 個地區選擇項目")
            
            logger.info(f"📝 找到 {len(context['input_fields'])} 個輸入欄位（包含地區選擇）")
            
            # 查找綠色按鈕（可能需要檢查 CSS 樣式）
            all_buttons = search_area.find_elements(By.CSS_SELECTOR, "button, input[type='button'], input[type='submit'], [role='button']")
            for button in all_buttons:
                if button.is_displayed() and button.is_enabled():
                    # 檢查按鈕是否是綠色的
                    if self.is_green_button(button):
                        context['green_buttons'].append(button)
                        logger.info(f"💚 找到綠色按鈕: '{self.get_element_text(button)}'")
                    
                    # 收集所有可點擊元素
                    context['all_clickable'].append(button)
            
            # 添加其他可點擊元素（連結等）
            other_clickable = search_area.find_elements(By.CSS_SELECTOR, "a[href], [onclick]")
            for element in other_clickable:
                if element.is_displayed():
                    context['all_clickable'].append(element)
            
            logger.info(f"🔗 總共找到 {len(context['all_clickable'])} 個可點擊元素")
            
        except Exception as e:
            logger.error(f"分析頁面上下文失敗: {e}")
        
        return context
    
    def execute_decision_logic(self, context):
        """根據決策邏輯執行動作"""
        try:
            # 🆕 決策邏輯 0a: 最高優先級 - 檢查是否有email欄位，如果有則優先填入
            email_fields = [field for field in context['input_fields'] 
                           if field.get_attribute('type') == 'email']
            if email_fields:
                email_field = email_fields[0]
                email_address = os.getenv('LOGIN_EMAIL', 'emile@pro360.com.tw')
                logger.info(f"🎯 決策 0a: 找到email欄位，最高優先級處理")
                result = self.interact_with_input(email_field)
                self.log_step("填入email欄位", email_address, "成功" if result else "失敗")
                if result:
                    # 填入email後，檢查是否有下一步按鈕可點擊
                    time.sleep(1)
                    context_after = self.analyze_current_context()
                    if context_after['next_buttons']:
                        logger.info("✅ Email填入成功，點擊下一步按鈕")
                        target_button = context_after['next_buttons'][0]
                        button_text = self.get_element_text(target_button)
                        click_result = self.click_element(target_button)
                        self.log_step("Email填入後點擊下一步", button_text, "成功" if click_result else "失敗")
                        return click_result
                return result
            
            # 🆕 決策邏輯 0b: 最高優先級 - 檢查是否有密碼欄位，如果有則優先填入
            password_fields = [field for field in context['input_fields'] 
                              if field.get_attribute('type') == 'password']
            if password_fields:
                password_field = password_fields[0]
                password = os.getenv('LOGIN_PASSWORD', 'pro360')
                logger.info(f"🎯 決策 0b: 找到密碼欄位，最高優先級處理")
                result = self.interact_with_input(password_field)
                self.log_step("填入密碼欄位", password, "成功" if result else "失敗")
                if result:
                    # 填入密碼後，檢查是否有下一步按鈕可點擊
                    time.sleep(1)
                    context_after = self.analyze_current_context()
                    if context_after['next_buttons']:
                        logger.info("✅ 密碼填入成功，點擊下一步按鈕")
                        target_button = context_after['next_buttons'][0]
                        button_text = self.get_element_text(target_button)
                        click_result = self.click_element(target_button)
                        self.log_step("密碼填入後點擊下一步", button_text, "成功" if click_result else "失敗")
                        return click_result
                return result
            
            # 🆕 決策邏輯 0c: 最高優先級 - 檢查是否有日期欄位，如果有則優先填入明天的日期
            date_fields = [field for field in context['input_fields'] 
                          if field.get_attribute('type') == 'date']
            if date_fields:
                date_field = date_fields[0]
                from datetime import datetime, timedelta
                tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                logger.info(f"🎯 決策 0c: 找到日期欄位，最高優先級處理")
                result = self.interact_with_input(date_field)
                self.log_step("填入日期欄位", tomorrow, "成功" if result else "失敗")
                if result:
                    # 填入日期後，檢查是否有下一步按鈕可點擊
                    time.sleep(1)
                    context_after = self.analyze_current_context()
                    if context_after['next_buttons']:
                        logger.info("✅ 日期填入成功，點擊下一步按鈕")
                        target_button = context_after['next_buttons'][0]
                        button_text = self.get_element_text(target_button)
                        click_result = self.click_element(target_button)
                        self.log_step("日期填入後點擊下一步", button_text, "成功" if click_result else "失敗")
                        return click_result
                return result
            
            # 🆕 決策邏輯 0d: 最高優先級 - 檢查是否有日曆組件，如果有則點擊第一個可點擊日期
            calendar_elements = self.find_calendar_dates()
            if calendar_elements:
                first_date = calendar_elements[0]
                date_text = self.get_element_text(first_date)
                logger.info(f"🎯 決策 0d: 找到日曆組件，點擊第一個可用日期")
                result = self.click_element(first_date)
                self.log_step("點擊日曆日期", date_text, "成功" if result else "失敗")
                if result:
                    # 點擊日期後，檢查是否有下一步按鈕可點擊
                    time.sleep(1)
                    context_after = self.analyze_current_context()
                    if context_after['next_buttons']:
                        logger.info("✅ 日曆日期選擇成功，點擊下一步按鈕")
                        target_button = context_after['next_buttons'][0]
                        button_text = self.get_element_text(target_button)
                        click_result = self.click_element(target_button)
                        self.log_step("日曆選擇後點擊下一步", button_text, "成功" if click_result else "失敗")
                        return click_result
                return result
            
            # 決策邏輯 1: 如果有可點擊的 "next" 按鈕，直接點擊
            if context['next_buttons']:
                target_button = context['next_buttons'][0]
                text = self.get_element_text(target_button)
                logger.info(f"🎯 決策 1: 點擊可用的下一步按鈕")
                
                # 🛑 記錄點擊的元素（用於循環檢測）
                self.record_clicked_element("點擊下一步按鈕", text, target_button)
                
                result = self.click_element(target_button)
                self.log_step("點擊下一步按鈕", text, "成功" if result else "失敗")
                return result
            
            # 決策邏輯 2: 如果有禁用的 "next" 按鈕，嘗試觸發輸入欄位
            if context['disabled_next_buttons'] and context['input_fields']:
                logger.info(f"🎯 決策 2: 下一步按鈕被禁用，嘗試觸發第一個輸入欄位")
                logger.info(f"   可用輸入欄位數量: {len(context['input_fields'])}")
                
                # 顯示所有可用的輸入欄位類型
                for i, field in enumerate(context['input_fields']):
                    field_type = field.get_attribute('type')
                    field_name = field.get_attribute('name') or 'none'
                    logger.info(f"   輸入欄位 {i+1}: type='{field_type}', name='{field_name}'")
                
                first_input = context['input_fields'][0]
                input_type = first_input.get_attribute('type')
                logger.info(f"   選擇第一個輸入欄位: type='{input_type}'")
                
                result = self.interact_with_input(first_input)
                if result:
                    # 檢查下一步按鈕是否變為可用
                    time.sleep(1)
                    context_after = self.analyze_current_context()
                    if context_after['next_buttons']:
                        logger.info("✅ 輸入欄位觸發成功，下一步按鈕已啟用")
                        target_button = context_after['next_buttons'][0]
                        button_text = self.get_element_text(target_button)
                        click_result = self.click_element(target_button)
                        self.log_step("觸發輸入後點擊下一步", button_text, "成功" if click_result else "失敗")
                        return click_result
                    else:
                        logger.info("⚠️  輸入欄位觸發後下一步按鈕仍未啟用")
                
                self.log_step("觸發輸入欄位", f"{input_type} 欄位", "成功" if result else "失敗")
                return result
            
            # 決策邏輯 3: 點擊綠色按鈕
            if context['green_buttons']:
                target_button = context['green_buttons'][0]
                text = self.get_element_text(target_button)
                logger.info(f"🎯 決策 3: 點擊綠色按鈕")
                result = self.click_element(target_button)
                self.log_step("點擊綠色按鈕", text, "成功" if result else "失敗")
                return result
            
            # 決策邏輯 4: 點擊最後一個可點擊元素
            if context['all_clickable']:
                target_element = context['all_clickable'][-1]
                text = self.get_element_text(target_element)
                logger.info(f"🎯 決策 4: 點擊最後一個可點擊元素")
                
                # 🛑 記錄點擊的元素（用於循環檢測）
                self.record_clicked_element("點擊最後元素", text, target_element)
                
                result = self.click_element(target_element)
                self.log_step("點擊最後元素", text, "成功" if result else "失敗")
                return result
            
            # 沒有可執行的動作
            logger.info("❌ 沒有找到可執行的動作")
            self.log_step("搜尋動作", "無", "失敗")
            return False
            
        except Exception as e:
            logger.error(f"執行決策邏輯失敗: {e}")
            self.log_step("執行決策", str(e), "錯誤")
            return False
    
    def interact_with_input(self, input_element):
        """與輸入元素互動"""
        try:
            input_type = input_element.get_attribute('type')
            tag_name = input_element.tag_name.lower()
            element_class = input_element.get_attribute('class') or ""
            element_text = self.get_element_text(input_element)
            
            # 🆕 檢查是否是地區/城市選擇元素
            if (tag_name == 'a' and 
                ('division-item' in element_class or 'area-picker' in element_class) or
                ('市' in element_text or '縣' in element_text or '區' in element_text)):
                logger.info(f"🏙️  點擊地區選擇: {element_text}")
                return self.click_element(input_element)
            
            elif input_type == 'radio':
                # 點擊單選按鈕
                logger.info("📻 點擊單選按鈕")
                return self.click_radio_button(input_element)
            
            elif input_type == 'checkbox':
                # 點擊核取方塊 - 使用多種方法處理隱藏的checkbox
                logger.info("☑️  點擊核取方塊")
                return self.click_checkbox(input_element)
            
            elif input_type == 'email':
                # 🆕 Email欄位特殊處理：自動填入環境變數中的email地址
                email_address = os.getenv('LOGIN_EMAIL', 'emile@pro360.com.tw')
                logger.info(f"📧 在email欄位自動填入: {email_address}")
                input_element.clear()
                input_element.send_keys(email_address)
                # 模擬Tab鍵或Enter鍵來觸發驗證
                input_element.send_keys(Keys.TAB)
                return True
            
            elif input_type == 'password':
                # 🆕 密碼欄位特殊處理：自動填入環境變數中的密碼
                password = os.getenv('LOGIN_PASSWORD', 'pro360')
                logger.info(f"🔐 在密碼欄位自動填入: {password}")
                input_element.clear()
                input_element.send_keys(password)
                # 模擬Tab鍵來觸發驗證
                input_element.send_keys(Keys.TAB)
                return True
            
            elif input_type == 'date':
                # 🆕 日期欄位特殊處理：自動填入明天的日期
                from datetime import datetime, timedelta
                tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                logger.info(f"📅 在日期欄位自動填入明天: {tomorrow}")
                input_element.clear()
                input_element.send_keys(tomorrow)
                # 模擬Tab鍵來觸發驗證
                input_element.send_keys(Keys.TAB)
                return True
            
            elif input_type in ['text', 'tel', 'number']:
                # 在其他文字欄位中輸入測試內容
                logger.info("📝 在文字欄位輸入內容")
                input_element.clear()
                input_element.send_keys("測試內容")
                return True
            
            elif tag_name == 'select':
                # 選擇下拉選單的第一個選項
                logger.info("📋 選擇下拉選單選項")
                from selenium.webdriver.support.ui import Select
                select = Select(input_element)
                if len(select.options) > 1:
                    select.select_by_index(1)  # 選擇第二個選項（跳過預設選項）
                return True
            
            # 如果都不是，嘗試直接點擊（可能是其他類型的選擇元素）
            elif tag_name in ['a', 'div', 'span'] and element_text:
                logger.info(f"🔘 點擊選擇元素: {element_text}")
                return self.click_element(input_element)
            
            return False
            
        except Exception as e:
            logger.error(f"與輸入元素互動失敗: {e}")
            return False
    
    def click_radio_button(self, radio_element):
        """點擊單選按鈕的多種方法"""
        try:
            # 方法1: 直接點擊
            try:
                radio_element.click()
                time.sleep(1)
                if radio_element.is_selected():
                    logger.info("✅ 直接點擊單選按鈕成功")
                    return True
            except:
                pass
            
            # 方法2: JavaScript 點擊
            try:
                self.driver.execute_script("arguments[0].click();", radio_element)
                time.sleep(1)
                if radio_element.is_selected():
                    logger.info("✅ JavaScript 點擊單選按鈕成功")
                    return True
            except:
                pass
            
            # 方法3: 點擊父 label
            try:
                parent = radio_element.find_element(By.XPATH, "..")
                if parent.tag_name.lower() == "label":
                    parent.click()
                    time.sleep(1)
                    if radio_element.is_selected():
                        logger.info("✅ 點擊 label 選中單選按鈕成功")
                        return True
            except:
                pass
            
            logger.warning("❌ 所有單選按鈕點擊方法都失敗")
            return False
            
        except Exception as e:
            logger.error(f"點擊單選按鈕失敗: {e}")
            return False
    
    def click_checkbox(self, checkbox_element):
        """點擊checkbox的多種方法，處理隱藏的checkbox"""
        try:
            checkbox_name = checkbox_element.get_attribute('name') or 'unknown'
            is_displayed = checkbox_element.is_displayed()
            
            # 方法1: 如果checkbox可見，直接點擊
            if is_displayed:
                try:
                    checkbox_element.click()
                    time.sleep(1)
                    if checkbox_element.is_selected():
                        logger.info("✅ 直接點擊可見checkbox成功")
                        return True
                except:
                    pass
            
            # 方法2: JavaScript 點擊（適用於隱藏的checkbox）
            try:
                self.driver.execute_script("arguments[0].click();", checkbox_element)
                time.sleep(1)
                logger.info("✅ JavaScript 點擊checkbox成功")
                return True
            except:
                pass
            
            # 方法3: JavaScript 直接設置checked狀態
            try:
                self.driver.execute_script("arguments[0].checked = !arguments[0].checked;", checkbox_element)
                # 觸發change事件
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", checkbox_element)
                time.sleep(1)
                logger.info("✅ JavaScript 設置checkbox狀態成功")
                return True
            except:
                pass
            
            # 方法4: 找到關聯的label並點擊
            try:
                # 嘗試通過for屬性找到關聯的label
                checkbox_id = checkbox_element.get_attribute('id')
                if checkbox_id:
                    label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{checkbox_id}']")
                    label.click()
                    time.sleep(1)
                    logger.info("✅ 點擊關聯label成功")
                    return True
            except:
                pass
            
            # 方法5: 找到父level的label或可點擊元素
            try:
                parent = checkbox_element.find_element(By.XPATH, "..")
                # 向上查找可點擊的父元素
                for i in range(3):  # 最多向上查找3級
                    if parent.tag_name.lower() in ['label', 'div', 'span'] and parent.is_displayed():
                        parent.click()
                        time.sleep(1)
                        logger.info(f"✅ 點擊父級元素 {parent.tag_name} 成功")
                        return True
                    parent = parent.find_element(By.XPATH, "..")
            except:
                pass
            
            logger.warning(f"❌ 所有checkbox點擊方法都失敗: {checkbox_name}")
            return False
            
        except Exception as e:
            logger.error(f"點擊checkbox失敗: {e}")
            return False
    
    def click_element(self, element):
        """點擊元素的多種方法"""
        try:
            # 滾動到元素位置
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # 方法1: 直接點擊
            try:
                element.click()
                logger.info("✅ 直接點擊成功")
                return True
            except ElementClickInterceptedException:
                pass
            
            # 方法2: JavaScript 點擊
            try:
                self.driver.execute_script("arguments[0].click();", element)
                logger.info("✅ JavaScript 點擊成功")
                return True
            except:
                pass
            
            # 方法3: ActionChains 點擊
            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(element).click().perform()
                logger.info("✅ ActionChains 點擊成功")
                return True
            except:
                pass
            
            logger.warning("❌ 所有點擊方法都失敗")
            return False
            
        except Exception as e:
            logger.error(f"點擊元素失敗: {e}")
            return False
    
    def detect_popup(self):
        """檢測彈出對話框"""
        popup_selectors = [
            "[role='dialog']",
            ".modal",
            ".popup",
            ".dialog",
            "*[style*='z-index']"
        ]
        
        for selector in popup_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if (element.is_displayed() and 
                        element.size['width'] > 200 and 
                        element.size['height'] > 100):
                        
                        z_index = self.driver.execute_script(
                            "return window.getComputedStyle(arguments[0]).zIndex;", element
                        )
                        
                        if z_index and z_index != 'auto' and int(z_index) > 100:
                            return element
            except:
                continue
        
        return None
    
    def get_element_text(self, element):
        """獲取元素的文字內容"""
        try:
            text = element.text.strip()
            if not text:
                text = (element.get_attribute("value") or 
                       element.get_attribute("aria-label") or 
                       element.get_attribute("title") or 
                       element.get_attribute("alt") or "")
            return text.strip()
        except:
            return ""
    
    def is_green_button(self, button):
        """檢查按鈕是否是綠色的"""
        try:
            # 檢查背景顏色
            bg_color = self.driver.execute_script(
                "return window.getComputedStyle(arguments[0]).backgroundColor;", button
            )
            
            # 檢查類別名稱是否包含綠色相關字詞
            class_name = button.get_attribute("class") or ""
            green_keywords = ['green', 'success', 'primary', 'btn-success', 'btn-primary']
            
            # 簡單的顏色檢測（這裡可以更精確）
            if bg_color and ('rgb(0, 128, 0)' in bg_color or 'rgb(40, 167, 69)' in bg_color):
                return True
            
            if any(keyword in class_name.lower() for keyword in green_keywords):
                return True
            
            return False
            
        except:
            return False
    
    def is_element_disabled(self, element):
        """檢查元素是否被禁用"""
        try:
            if element.get_attribute("disabled"):
                return True
            
            # 檢查 aria-disabled
            if element.get_attribute("aria-disabled") == "true":
                return True
            
            # 檢查類別名稱
            class_name = element.get_attribute("class") or ""
            if "disabled" in class_name.lower():
                return True
            
            return False
            
        except:
            return True
    
    def record_clicked_element(self, action_type, element_text, element):
        """記錄點擊的元素（用於循環檢測）- 重點記錄頁面可點擊元素集合"""
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            # 🎯 關鍵：獲取當前頁面所有可點擊元素的簽名
            clickable_elements_signature = self.get_clickable_elements_hash()
            
            element_info = {
                'step': self.current_step,
                'action_type': action_type,
                'text': element_text,
                'tag': element.tag_name,
                'href': element.get_attribute('href') or '',
                'class': element.get_attribute('class') or '',
                'url': current_url,
                'page_title': page_title,
                'clickable_elements_hash': clickable_elements_signature,  # 這是關鍵！
                'timestamp': datetime.now().isoformat()
            }
            
            self.clicked_elements_history.append(element_info)
            
            # 限制歷史記錄長度
            if len(self.clicked_elements_history) > 10:
                self.clicked_elements_history.pop(0)
                
        except Exception as e:
            logger.error(f"記錄點擊元素失敗: {e}")
    
    def get_clickable_elements_hash(self):
        """獲取當前頁面所有可點擊元素的hash簽名"""
        try:
            # 尋找所有可點擊元素
            clickable_selectors = [
                "button",
                "input[type='button']", 
                "input[type='submit']",
                "input[type='radio']",
                "input[type='checkbox']",
                "a[href]",
                "[role='button']",
                "[onclick]",
                "select"
            ]
            
            clickable_elements = []
            for selector in clickable_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        # 建立元素的唯一識別
                        element_signature = {
                            'tag': elem.tag_name,
                            'text': self.get_element_text(elem)[:50],  # 只取前50字符
                            'type': elem.get_attribute('type') or '',
                            'href': elem.get_attribute('href') or '',
                            'class': elem.get_attribute('class') or '',
                            'id': elem.get_attribute('id') or '',
                            'value': elem.get_attribute('value') or ''
                        }
                        clickable_elements.append(str(element_signature))
            
            # 排序後生成hash，確保順序不影響結果
            clickable_elements.sort()
            elements_string = '|'.join(clickable_elements)
            
            return hash(elements_string)
            
        except Exception as e:
            logger.error(f"獲取可點擊元素hash失敗: {e}")
            return 0
    
    def find_calendar_dates(self):
        """尋找日曆組件中的可點擊日期"""
        try:
            # 檢測彈出對話框
            popup = self.detect_popup()
            search_area = popup if popup else self.driver
            
            calendar_date_selectors = [
                # React Calendar 常見的日期按鈕選擇器
                ".react-calendar__month-view__days__day",
                ".react-calendar__tile",
                "[class*='calendar'][class*='day']:not([disabled])",
                "[class*='date']:not([disabled])",
                # 一般日曆選擇器
                ".calendar-day:not([disabled])",
                ".day:not([disabled])",
                "[role='gridcell']:not([disabled])",
                # 包含數字且可點擊的按鈕（可能是日期）
                "button[class*='day']:not([disabled])",
                "button[class*='date']:not([disabled])"
            ]
            
            clickable_dates = []
            
            for selector in calendar_date_selectors:
                elements = search_area.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        # 檢查是否包含數字（可能是日期）
                        text = self.get_element_text(elem).strip()
                        
                        # 如果文字是1-31的數字，很可能是日期
                        if text.isdigit() and 1 <= int(text) <= 31:
                            clickable_dates.append(elem)
                        # 或者如果有日期相關的類名
                        elif ('date' in elem.get_attribute('class').lower() or 
                              'day' in elem.get_attribute('class').lower() or
                              'calendar' in elem.get_attribute('class').lower()):
                            clickable_dates.append(elem)
            
            if clickable_dates:
                logger.info(f"📅 找到 {len(clickable_dates)} 個可點擊的日曆日期")
                return clickable_dates
            
            return []
            
        except Exception as e:
            logger.error(f"尋找日曆日期失敗: {e}")
            return []
    
    def detect_loop(self):
        """🎯 完全基於可點擊元素集合的循環檢測 - 不關心點擊了什麼，只關心可點擊選項是否相同"""
        if len(self.clicked_elements_history) < 4:
            return False
        
        # 🔍 核心檢測：可點擊元素集合是否完全相同
        # 如果最近幾次操作的可點擊元素完全一樣，才是真正的循環
        recent_clicks = self.clicked_elements_history[-4:]
        recent_clickable_hashes = [click['clickable_elements_hash'] for click in recent_clicks]
        
        # 如果最近4次操作的可點擊元素集合完全相同
        if len(set(recent_clickable_hashes)) == 1:
            logger.warning(f"🔄 檢測到真正的循環！")
            logger.warning(f"   最近4次操作，頁面可點擊元素集合完全相同")
            logger.warning(f"   這意味著無論點擊什麼，頁面選項都沒有改變")
            
            # 顯示最近的操作（但不基於操作內容判斷）
            actions = [f"步驟{click['step']}" for click in recent_clicks]
            logger.warning(f"   涉及步驟: {actions}")
            
            self.is_loop_detected = True
            return True
        
        # 🔍 擴展檢測：檢查更長的循環（6次操作中有重複的可點擊元素模式）
        if len(self.clicked_elements_history) >= 6:
            recent_6_clicks = self.clicked_elements_history[-6:]
            clickable_hashes = [click['clickable_elements_hash'] for click in recent_6_clicks]
            
            # 統計每種可點擊元素集合出現的次數
            hash_counts = {}
            for hash_val in clickable_hashes:
                hash_counts[hash_val] = hash_counts.get(hash_val, 0) + 1
            
            # 如果某種可點擊元素集合出現3次以上
            for hash_val, count in hash_counts.items():
                if count >= 3:
                    logger.warning(f"🔄 檢測到較長的循環模式！")
                    logger.warning(f"   同一種可點擊元素集合在最近6步中出現 {count} 次")
                    
                    # 找出是哪些步驟
                    involved_steps = [click['step'] for click in recent_6_clicks 
                                    if click['clickable_elements_hash'] == hash_val]
                    logger.warning(f"   涉及步驟: {involved_steps}")
                    
                    self.is_loop_detected = True
                    return True
        
        # ✅ 只要可點擊元素集合有變化，就不是循環
        # 表單進展、頁面變化都會改變可點擊元素集合
        return False

    def generate_report(self):
        """生成測試報告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"autopilot_report_{timestamp}.json"
            
            import json
            
            # 擴展報告內容，包含循環檢測資訊
            report_data = {
                "test_log": self.test_log,
                "loop_detection": {
                    "loop_detected": self.is_loop_detected,
                    "clicked_elements_history": self.clicked_elements_history
                },
                "summary": {
                    "total_steps": len(self.test_log),
                    "loop_detected": self.is_loop_detected,
                    "test_completed": True
                }
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📊 測試報告已生成: {report_file}")
            
            # 生成簡單摘要
            logger.info(f"\n📋 測試摘要:")
            logger.info(f"   總步驟數: {len(self.test_log)}")
            success_count = sum(1 for log in self.test_log if log['result'] == '成功')
            logger.info(f"   成功步驟: {success_count}")
            logger.info(f"   成功率: {success_count/len(self.test_log)*100:.1f}%")
            
            if self.is_loop_detected:
                logger.info(f"   🔄 循環檢測: 是")
                logger.info(f"   點擊歷史: {len(self.clicked_elements_history)} 個記錄")
            else:
                logger.info(f"   🔄 循環檢測: 否")
            
        except Exception as e:
            logger.error(f"生成報告失敗: {e}")
    
    def wait_and_close(self):
        """等待用戶觀察，然後關閉瀏覽器"""
        try:
            print("\n" + "="*60)
            print("🔍 自動駕駛測試完成！請檢查瀏覽器視窗中的結果")
            
            # 🛑 如果檢測到循環，顯示循環檢測資訊
            if self.is_loop_detected:
                print("\n🔄 循環檢測報告:")
                print("=" * 50)
                print("❌ 檢測到重複操作循環，測試已自動停止")
                
                if self.clicked_elements_history:
                    print("\n📋 最近的點擊記錄:")
                    recent_clicks = self.clicked_elements_history[-5:] if len(self.clicked_elements_history) >= 5 else self.clicked_elements_history
                    for click in recent_clicks:
                        print(f"   步驟 {click['step']}: {click['action_type']} -> {click['text']}")
                
                print("\n💡 循環檢測成功防止了無限測試！")
                print("💡 建議：檢查網站的導航邏輯或修改測試策略")
                print("=" * 50)
            
            print("按 Enter 鍵關閉瀏覽器...")
            input()
        except KeyboardInterrupt:
            pass
        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("🤖 智能自動駕駛測試程式")
    print("="*60)
    
    # 從環境變數讀取設定
    start_url = os.getenv('DEFAULT_TEST_URL', 'https://www.pro360.com.tw/?category=cleaning')
    
    print(f"🌐 起始 URL: {start_url}")
    print(f"📐 視窗寬度: {os.getenv('WINDOW_WIDTH', 640)}px")
    print(f"🖥️  無頭模式: {os.getenv('HEADLESS_MODE', 'False')}")
    print("\n🚀 開始自動駕駛測試...")
    
    autopilot = AutoPilotTester()
    try:
        autopilot.start_autopilot(start_url)
    except Exception as e:
        logger.error(f"自動駕駛測試失敗: {e}")
        autopilot.wait_and_close()

if __name__ == "__main__":
    main() 