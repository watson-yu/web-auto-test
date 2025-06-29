"""
網頁抓取模組 - 用於抓取網頁並提取可點擊的元素
"""
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, ElementClickInterceptedException
import time
import random
from typing import List, Dict, Optional, Tuple
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    """網頁抓取器類別"""
    
    def __init__(self, use_selenium: bool = True, headless: bool = True, window_width: int = 640):
        """
        初始化網頁抓取器
        
        Args:
            use_selenium: 是否使用 Selenium（適用於動態內容）
            headless: 是否無頭模式運行瀏覽器
            window_width: 瀏覽器視窗寬度（像素）
        """
        self.use_selenium = use_selenium
        self.headless = headless
        self.window_width = window_width
        self.driver = None
    
    def _get_screen_height(self) -> int:
        """
        獲取螢幕高度，如果無法獲取則返回預設值
        
        Returns:
            螢幕高度（像素）
        """
        try:
            # 嘗試使用 tkinter 獲取螢幕大小
            import tkinter as tk
            root = tk.Tk()
            screen_height = root.winfo_screenheight()
            root.destroy()
            logger.info(f"檢測到螢幕高度: {screen_height}px")
            return screen_height
        except Exception:
            # 如果無法獲取螢幕大小，使用預設值
            default_height = 1080
            logger.info(f"無法檢測螢幕高度，使用預設值: {default_height}px")
            return default_height
        
    def _setup_driver(self) -> webdriver.Chrome:
        """設定 Chrome 瀏覽器驅動"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # 獲取螢幕高度並設定用戶定義的視窗寬度
        screen_height = self._get_screen_height()
        chrome_options.add_argument(f'--window-size={self.window_width},{screen_height}')
        logger.info(f"設定瀏覽器視窗大小: {self.window_width}x{screen_height}")
        
        try:
            # 優先嘗試使用 webdriver-manager 自動管理 ChromeDriver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                logger.info("使用 webdriver-manager 自動管理 ChromeDriver")
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except ImportError:
                logger.info("webdriver-manager 未安裝，使用系統 ChromeDriver")
                driver = webdriver.Chrome(options=chrome_options)
            
            # 確保視窗大小設定正確（有時 Chrome options 可能不完全生效）
            driver.set_window_size(self.window_width, screen_height)
            logger.info(f"✅ 瀏覽器視窗已設定為 {self.window_width}x{screen_height}")
            
            return driver
            
        except WebDriverException as e:
            logger.error(f"無法啟動 Chrome 瀏覽器: {e}")
            logger.error("建議解決方案:")
            logger.error("1. 安裝 webdriver-manager: pip install webdriver-manager")
            logger.error("2. 或手動安裝 ChromeDriver: https://chromedriver.chromium.org/")
            logger.error("3. 確保 Chrome 瀏覽器已安裝")
            raise
    
    def fetch_page(self, url: str, wait_time: int = 10) -> Optional[str]:
        """
        抓取網頁內容
        
        Args:
            url: 要抓取的網頁 URL
            wait_time: 等待頁面載入的時間（秒）
            
        Returns:
            網頁的 HTML 內容，如果失敗則返回 None
        """
        try:
            if self.use_selenium:
                return self._fetch_with_selenium(url, wait_time)
            else:
                return self._fetch_with_requests(url)
        except Exception as e:
            logger.error(f"抓取網頁失敗: {e}")
            return None
    
    def _fetch_with_selenium(self, url: str, wait_time: int) -> str:
        """使用 Selenium 抓取網頁"""
        self.driver = self._setup_driver()
        try:
            logger.info(f"正在載入網頁: {url}")
            self.driver.get(url)
            
            # 等待頁面載入
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 額外等待動態內容載入
            time.sleep(2)
            
            return self.driver.page_source
        except TimeoutException:
            logger.warning(f"網頁載入超時: {url}")
            return self.driver.page_source if self.driver else ""
        finally:
            if self.driver:
                self.driver.quit()
    
    def _fetch_with_requests(self, url: str) -> str:
        """使用 requests 抓取網頁"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    
    def extract_clickable_elements(self, html_content: str, base_url: str = "") -> List[Dict[str, str]]:
        """
        從 HTML 內容中提取可點擊的元素
        
        Args:
            html_content: HTML 內容
            base_url: 基礎 URL，用於處理相對連結
            
        Returns:
            包含可點擊元素資訊的字典列表
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        clickable_elements = []
        
        # 提取所有連結
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)
            title = link.get('title', '')
            
            # 處理相對連結
            if href.startswith('/') and base_url:
                href = base_url.rstrip('/') + href
            elif href.startswith('./') and base_url:
                href = base_url.rstrip('/') + '/' + href[2:]
            
            clickable_elements.append({
                'type': 'link',
                'tag': 'a',
                'text': text,
                'href': href,
                'title': title,
                'id': link.get('id', ''),
                'class': ' '.join(link.get('class', [])),
            })
        
        # 提取按鈕
        buttons = soup.find_all(['button', 'input'])
        for button in buttons:
            if button.name == 'input' and button.get('type') not in ['button', 'submit', 'reset']:
                continue
                
            text = button.get_text(strip=True) if button.name == 'button' else button.get('value', '')
            
            clickable_elements.append({
                'type': 'button',
                'tag': button.name,
                'text': text,
                'href': '',
                'title': button.get('title', ''),
                'id': button.get('id', ''),
                'class': ' '.join(button.get('class', [])),
                'input_type': button.get('type', '') if button.name == 'input' else '',
            })
        
        # 提取其他可點擊元素（有 onclick 事件的）
        onclick_elements = soup.find_all(attrs={'onclick': True})
        for element in onclick_elements:
            if element.name in ['a', 'button', 'input']:
                continue  # 已經在上面處理過了
                
            text = element.get_text(strip=True)
            clickable_elements.append({
                'type': 'clickable',
                'tag': element.name,
                'text': text,
                'href': '',
                'title': element.get('title', ''),
                'id': element.get('id', ''),
                'class': ' '.join(element.get('class', [])),
                'onclick': element.get('onclick', ''),
            })
        
        logger.info(f"找到 {len(clickable_elements)} 個可點擊元素")
        return clickable_elements
    
    def get_clickable_elements_from_url(self, url: str, wait_time: int = 10) -> List[Dict[str, str]]:
        """
        從指定 URL 獲取所有可點擊元素
        
        Args:
            url: 要分析的網頁 URL
            wait_time: 等待頁面載入的時間（秒）
            
        Returns:
            包含可點擊元素資訊的字典列表
        """
        html_content = self.fetch_page(url, wait_time)
        if not html_content:
            return []
        
        # 從 URL 提取基礎 URL
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        return self.extract_clickable_elements(html_content, base_url)
    
    def random_click_and_continue(self, elements: List[Dict[str, str]], initial_url: str = "", wait_time: int = 10) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        """
        隨機選擇一個可點擊元素進行點擊，並返回新頁面的可點擊元素
        
        Args:
            elements: 可點擊元素列表
            initial_url: 初始網頁 URL（用於處理相對連結）
            wait_time: 等待頁面載入的時間（秒）
            
        Returns:
            Tuple[點擊的元素資訊, 新頁面的可點擊元素列表]
        """
        if not elements:
            logger.warning("沒有可點擊的元素")
            return {}, []
        
        # 過濾掉沒有實際連結或動作的元素（包括彈出框元素和表單元素）
        clickable_elements = [
            elem for elem in elements 
            if (elem.get('href') or elem.get('onclick') or 
                elem['type'] in ['button', 'popup_button', 'popup_link', 'popup_clickable',
                               'popup_radio', 'popup_checkbox', 'popup_input', 'popup_select', 'popup_textarea'])
        ]
        
        if not clickable_elements:
            logger.warning("沒有有效的可點擊元素")
            return {}, []
        
        # 隨機選擇一個元素
        selected_element = random.choice(clickable_elements)
        logger.info(f"隨機選擇元素: [{selected_element['type']}] {selected_element['text'][:50]}")
        
        try:
            # 使用 Selenium 點擊元素
            new_elements = self._click_element_and_get_new_elements(
                selected_element, initial_url, wait_time
            )
            
            return selected_element, new_elements
            
        except Exception as e:
            logger.error(f"點擊元素失敗: {e}")
            return selected_element, []
    
    def _click_element_and_get_new_elements(self, element: Dict[str, str], base_url: str, wait_time: int) -> List[Dict[str, str]]:
        """
        點擊指定元素並獲取新頁面的可點擊元素
        
        Args:
            element: 要點擊的元素資訊
            base_url: 基礎 URL
            wait_time: 等待時間
            
        Returns:
            新頁面的可點擊元素列表
        """
        if not self.use_selenium:
            logger.warning("需要使用 Selenium 來點擊元素")
            return []
        
        self.driver = self._setup_driver()
        
        try:
            # 如果元素有 href，直接導航到該 URL
            if element.get('href') and element['href'].startswith(('http://', 'https://')):
                target_url = element['href']
                logger.info(f"導航到連結: {target_url}")
                self.driver.get(target_url)
            
            # 如果是相對連結，組合完整 URL
            elif element.get('href') and base_url:
                href = element['href']
                if href.startswith('/'):
                    target_url = base_url.rstrip('/') + href
                elif href.startswith('./'):
                    target_url = base_url.rstrip('/') + '/' + href[2:]
                else:
                    target_url = base_url.rstrip('/') + '/' + href
                
                logger.info(f"導航到相對連結: {target_url}")
                self.driver.get(target_url)
            
            # 如果沒有 href，嘗試在當前頁面找到並點擊元素
            else:
                if base_url:
                    self.driver.get(base_url)
                
                # 等待頁面載入
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 嘗試通過不同方式找到元素
                web_element = self._find_web_element(element)
                
                if web_element:
                    # 滾動到元素位置
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", web_element)
                    time.sleep(1)
                    
                    # 點擊元素
                    logger.info(f"點擊元素: {element['text'][:30]}")
                    web_element.click()
                else:
                    logger.warning(f"無法找到要點擊的元素: {element}")
                    return []
            
            # 等待新頁面載入
            time.sleep(2)
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 獲取當前 URL 作為新的基礎 URL
            current_url = self.driver.current_url
            from urllib.parse import urlparse
            parsed_url = urlparse(current_url)
            new_base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # 提取新頁面的可點擊元素
            page_source = self.driver.page_source
            new_elements = self.extract_clickable_elements(page_source, new_base_url)
            
            logger.info(f"在新頁面找到 {len(new_elements)} 個可點擊元素")
            return new_elements
            
        except TimeoutException:
            logger.warning("頁面載入超時")
            return []
        except (NoSuchElementException, ElementClickInterceptedException) as e:
            logger.warning(f"無法點擊元素: {e}")
            return []
        except Exception as e:
            logger.error(f"點擊過程中發生錯誤: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _find_web_element(self, element: Dict[str, str]):
        """
        在網頁中找到對應的 WebElement
        
        Args:
            element: 元素資訊字典
            
        Returns:
            找到的 WebElement 或 None
        """
        try:
            # 🎯 專門處理表單元素
            if element['type'].startswith('popup_'):
                return self._find_form_web_element(element)
            
            # 優先使用 ID 查找
            if element.get('id'):
                return self.driver.find_element(By.ID, element['id'])
            
            # 使用 CSS 類別查找
            if element.get('class'):
                class_name = element['class'].replace(' ', '.')
                elements_by_class = self.driver.find_elements(By.CSS_SELECTOR, f".{class_name}")
                # 通過文字內容進一步篩選
                for elem in elements_by_class:
                    if element['text'] in elem.text:
                        return elem
            
            # 使用標籤和文字內容查找
            if element.get('text'):
                tag = element.get('tag', 'a')
                xpath = f"//{tag}[contains(text(), '{element['text'][:20]}')]"
                return self.driver.find_element(By.XPATH, xpath)
            
            # 使用 href 查找連結
            if element.get('href') and element['tag'] == 'a':
                href = element['href']
                if href.startswith('/'):
                    xpath = f"//a[@href='{href}']"
                else:
                    xpath = f"//a[contains(@href, '{href.split('/')[-1]}')]"
                return self.driver.find_element(By.XPATH, xpath)
                
        except NoSuchElementException:
            pass
        
        return None

    def _find_form_web_element(self, element: Dict[str, str]):
        """
        專門用於尋找表單元素的 WebElement
        
        Args:
            element: 表單元素資訊字典
            
        Returns:
            找到的 WebElement 或 None
        """
        try:
            element_type = element['type']
            input_type = element.get('input_type', '')
            name = element.get('name', '')
            value = element.get('value', '')
            element_id = element.get('id', '')
            text = element.get('text', '')
            
            logger.debug(f"🔍 尋找表單元素: type={element_type}, input_type={input_type}, name={name}, value={value}")
            
            # 優先使用 ID
            if element_id:
                try:
                    found_element = self.driver.find_element(By.ID, element_id)
                    logger.debug(f"✅ 通過ID找到元素: {element_id}")
                    return found_element
                except NoSuchElementException:
                    pass
            
            # 使用 name 和 value 組合查找（適用於單選按鈕和核取方塊）
            if name and value and input_type in ['radio', 'checkbox']:
                try:
                    selector = f"input[type='{input_type}'][name='{name}'][value='{value}']"
                    found_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.debug(f"✅ 通過name+value找到元素: {selector}")
                    return found_element
                except NoSuchElementException:
                    pass
            
            # 使用 name 查找（適用於輸入框）
            if name and input_type in ['text', 'email', 'tel', 'number']:
                try:
                    selector = f"input[type='{input_type}'][name='{name}']"
                    found_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.debug(f"✅ 通過name找到輸入元素: {selector}")
                    return found_element
                except NoSuchElementException:
                    pass
            
            # 通過標籤文字查找（特別適用於單選按鈕）
            if input_type == 'radio' and text:
                try:
                    # 方法1：找到包含文字的標籤，然後找關聯的單選按鈕或直接返回 label（點擊 label 也能選中單選按鈕）
                    xpath = f"//label[contains(text(), '{text}')]"
                    labels = self.driver.find_elements(By.XPATH, xpath)
                    for label in labels:
                        # 檢查 label 的 for 屬性
                        label_for = label.get_attribute('for')
                        if label_for:
                            try:
                                radio_element = self.driver.find_element(By.ID, label_for)
                                if radio_element.get_attribute('type') == 'radio':
                                    logger.debug(f"✅ 通過label找到單選按鈕: {text}")
                                    return radio_element
                            except:
                                pass
                        
                        # 檢查 label 內部是否包含單選按鈕
                        try:
                            radio_element = label.find_element(By.CSS_SELECTOR, "input[type='radio']")
                            logger.debug(f"✅ 在label內找到單選按鈕: {text}")
                            # 對於包含在 label 內的單選按鈕，返回 label 會更可靠
                            if label.is_displayed():
                                logger.debug(f"✅ 返回可見的label元素進行點擊: {text}")
                                return label
                            return radio_element
                        except:
                            pass
                    
                    # 方法2：直接通過文字查找附近的單選按鈕
                    xpath = f"//input[@type='radio'][following-sibling::text()[contains(., '{text}')] or preceding-sibling::text()[contains(., '{text}')]]"
                    try:
                        found_element = self.driver.find_element(By.XPATH, xpath)
                        logger.debug(f"✅ 通過文字附近找到單選按鈕: {text}")
                        return found_element
                    except:
                        pass
                        
                except Exception as e:
                    logger.debug(f"通過文字查找單選按鈕失敗: {e}")
            
            # 最後嘗試：使用類別查找
            if element.get('class'):
                try:
                    class_name = element['class'].replace(' ', '.')
                    selector = f".{class_name}"
                    found_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.debug(f"✅ 通過class找到元素: {selector}")
                    return found_element
                except NoSuchElementException:
                    pass
            
            logger.warning(f"❌ 無法找到表單元素: {element}")
            return None
            
        except Exception as e:
            logger.error(f"尋找表單元素時發生錯誤: {e}")
            return None

    def _handle_form_element_click(self, selected_element: Dict[str, str], web_element, wait_time: int) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        """
        專門處理表單元素的點擊邏輯
        
        Args:
            selected_element: 選中的表單元素資訊
            web_element: 找到的 WebElement
            wait_time: 等待時間
            
        Returns:
            Tuple[點擊的元素資訊, 更新後的可點擊元素列表]
        """
        try:
            element_type = selected_element.get('input_type', '')
            
            # 執行點擊操作
            web_element.click()
            logger.info(f"✅ 成功點擊表單元素: {selected_element['text'][:30]}")
            
            # 🎯 針對不同類型的表單元素進行特殊處理
            if element_type == 'radio' or selected_element.get('type') == 'popup_radio':
                logger.info("📻 已選擇單選按鈕，等待頁面狀態更新...")
                time.sleep(2)  # 等待單選按鈕狀態更新
                
            elif element_type == 'checkbox' or selected_element.get('type') == 'popup_checkbox':
                logger.info("☑️  已切換核取方塊，等待頁面狀態更新...")
                time.sleep(1)
                
            elif element_type in ['text', 'email', 'tel', 'number', 'popup_input', 'popup_email']:
                logger.info("📝 已聚焦輸入框，準備輸入內容...")
                
                # 🎯 最高優先級：Email 欄位自動填入
                if (element_type in ['email', 'popup_email'] or 
                    'email' in selected_element.get('name', '').lower() or
                    'email' in selected_element.get('input_type', '').lower()):
                    try:
                        email_address = "emile@pro360.com.tw"
                        web_element.clear()  # 清空現有內容
                        web_element.send_keys(email_address)
                        logger.info(f"🎯 最高優先級 - 自動填入email地址: {email_address}")
                        time.sleep(2)  # 等待輸入完成
                    except Exception as e:
                        logger.error(f"❌ email自動填入失敗: {e}")
                        time.sleep(1)
                else:
                    # 其他類型的輸入框處理
                    logger.info(f"📝 {element_type} 輸入框已聚焦，等待用戶操作...")
                    time.sleep(1)
                
            else:
                time.sleep(1)
            
            # 🔄 重新檢測彈出框內的元素（因為表單狀態可能已改變）
            logger.info("🔄 重新檢測彈出框內的元素...")
            
            # 重新檢測彈出框
            popup_element = self._detect_popup_dialog()
            if popup_element:
                new_elements = self._extract_popup_elements(popup_element)
                logger.info(f"🎯 表單點擊後找到 {len(new_elements)} 個可點擊元素")
                
                # 檢查是否有啟用的「下一步」按鈕
                next_buttons = [elem for elem in new_elements 
                              if ('下一步' in elem['text'] or 'next' in elem['text'].lower()) 
                              and elem['type'] in ['popup_button', 'popup_link']]
                
                if next_buttons:
                    logger.info("🎉 檢測到可能已啟用的「下一步」按鈕！")
                
                return selected_element, new_elements
            else:
                # 如果沒有彈出框了，可能是表單提交了，檢測主頁面
                logger.info("🔄 彈出框可能已關閉，檢測主頁面元素...")
                main_elements = self._extract_elements_from_current_page()
                return selected_element, main_elements
            
        except Exception as e:
            logger.error(f"處理表單元素點擊時發生錯誤: {e}")
            # 發生錯誤時，嘗試重新檢測頁面元素
            try:
                new_elements = self._extract_elements_from_current_page()
                return selected_element, new_elements
            except:
                return selected_element, []

    def _detect_popup_dialog(self) -> Optional[any]:
        """
        檢測頁面上是否有彈出對話框/模態視窗
        
        Returns:
            如果檢測到彈出對話框，返回包含該對話框的 WebElement，否則返回 None
        """
        if not self.driver:
            return None
        
        try:
            # 常見的彈出對話框選擇器
            popup_selectors = [
                # 模態對話框
                "[role='dialog']",
                ".modal",
                ".popup",
                ".dialog", 
                ".overlay",
                ".lightbox",
                # 高 z-index 元素（通常是彈出內容）
                "*[style*='z-index']",
                # Bootstrap 模態
                ".modal-dialog",
                ".modal-content",
                # 常見的彈出容器
                ".popup-container",
                ".dialog-container",
                ".overlay-container",
                # jQuery UI 對話框
                ".ui-dialog",
                # 自定義彈出框
                "[data-popup]",
                "[data-modal]",
                # 固定定位的元素（可能是彈出框）
                "*[style*='position: fixed']",
                "*[style*='position:fixed']"
            ]
            
            logger.info("🔍 檢測頁面是否有彈出對話框...")
            
            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        # 檢查元素是否可見且有實際內容
                        if (element.is_displayed() and 
                            element.size['width'] > 200 and 
                            element.size['height'] > 100):
                            
                            # 檢查 z-index 是否足夠高（表示在最上層）
                            z_index = self.driver.execute_script(
                                "return window.getComputedStyle(arguments[0]).zIndex;", element
                            )
                            
                            # 檢查是否位於視窗中央區域（彈出框通常在中央）
                            location = element.location
                            size = element.size
                            window_width = self.driver.execute_script("return window.innerWidth;")
                            window_height = self.driver.execute_script("return window.innerHeight;")
                            
                            center_x = location['x'] + size['width'] // 2
                            center_y = location['y'] + size['height'] // 2
                            window_center_x = window_width // 2
                            window_center_y = window_height // 2
                            
                            # 判斷是否接近視窗中心
                            x_distance = abs(center_x - window_center_x)
                            y_distance = abs(center_y - window_center_y)
                            
                            is_centered = (x_distance < window_width * 0.3 and 
                                         y_distance < window_height * 0.3)
                            
                            # 檢查是否有較高的 z-index 或處於中央位置
                            if (z_index and z_index != 'auto' and int(z_index) > 100) or is_centered:
                                logger.info(f"🎯 檢測到彈出對話框: {selector}, z-index: {z_index}, 尺寸: {size['width']}x{size['height']}")
                                return element
                                
                except Exception:
                    continue
            
            # 額外檢查：查找包含特定文字的對話框
            dialog_text_patterns = [
                "確認", "取消", "關閉", "同意", "拒絕", "接受", 
                "登入", "註冊", "繼續", "下一步", "完成",
                "confirm", "cancel", "close", "accept", "reject",
                "login", "register", "continue", "next", "finish"
            ]
            
            for pattern in dialog_text_patterns:
                try:
                    xpath = f"//*[contains(text(), '{pattern}') and (contains(@class, 'modal') or contains(@class, 'dialog') or contains(@class, 'popup'))]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed():
                            # 找到包含對話框元素的父容器
                            parent = element
                            for _ in range(5):  # 向上查找5層
                                try:
                                    parent = parent.find_element(By.XPATH, "..")
                                    if parent and parent.size['width'] > 300 and parent.size['height'] > 200:
                                        logger.info(f"🎯 透過文字模式檢測到彈出對話框: 包含 '{pattern}'")
                                        return parent
                                except:
                                    break
                except Exception:
                    continue
            
            logger.info("✅ 未檢測到彈出對話框，將處理主頁面內容")
            return None
            
        except Exception as e:
            logger.error(f"檢測彈出對話框時發生錯誤: {e}")
            return None

    def _is_element_disabled(self, element) -> bool:
        """
        檢查元素是否被禁用
        
        Args:
            element: Selenium WebElement
            
        Returns:
            True 如果元素被禁用，False 如果元素可用
        """
        try:
            # 檢查 disabled 屬性
            disabled_attr = element.get_attribute("disabled")
            if disabled_attr is not None and disabled_attr != "false":
                logger.debug(f"元素被禁用 (disabled屬性): {element.text.strip()[:20]}")
                return True
            
            # 檢查 aria-disabled 屬性
            aria_disabled = element.get_attribute("aria-disabled")
            if aria_disabled == "true":
                logger.debug(f"元素被禁用 (aria-disabled): {element.text.strip()[:20]}")
                return True
            
            # 檢查是否有 disabled 類別
            class_name = element.get_attribute("class") or ""
            disabled_classes = ["disabled", "btn-disabled", "inactive", "not-allowed"]
            if any(cls in class_name.lower() for cls in disabled_classes):
                logger.debug(f"元素被禁用 (CSS類別): {element.text.strip()[:20]}")
                return True
            
            # 檢查 CSS 樣式中的 pointer-events 和 cursor
            try:
                pointer_events = self.driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).pointerEvents;", element
                )
                cursor = self.driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).cursor;", element
                )
                
                if pointer_events == "none":
                    logger.debug(f"元素被禁用 (pointer-events: none): {element.text.strip()[:20]}")
                    return True
                
                if cursor in ["not-allowed", "default"] and element.tag_name.lower() in ["button", "a"]:
                    # 對於按鈕和連結，not-allowed 或 default cursor 可能表示禁用
                    logger.debug(f"元素可能被禁用 (cursor: {cursor}): {element.text.strip()[:20]}")
                    # 這裡不直接返回 True，而是進行進一步檢查
            except:
                pass
            
            # 檢查按鈕的顏色是否表示禁用狀態
            if element.tag_name.lower() == "button":
                try:
                    # 獲取背景顏色
                    bg_color = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).backgroundColor;", element
                    )
                    opacity = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).opacity;", element
                    )
                    
                    # 檢查透明度是否過低（表示禁用）
                    if opacity and float(opacity) < 0.6:
                        logger.debug(f"按鈕透明度過低，可能被禁用 (opacity: {opacity}): {element.text.strip()[:20]}")
                        return True
                    
                    # 檢查是否是灰色背景（常見的禁用狀態）
                    if bg_color and ("rgb(128" in bg_color or "rgb(192" in bg_color or "rgb(211" in bg_color):
                        logger.debug(f"按鈕背景色表示禁用 (bg: {bg_color}): {element.text.strip()[:20]}")
                        return True
                        
                except:
                    pass
            
            # 嘗試檢查是否可以點擊
            try:
                # 檢查元素是否可以接收點擊事件
                is_clickable = self.driver.execute_script("""
                    var element = arguments[0];
                    var style = window.getComputedStyle(element);
                    return style.pointerEvents !== 'none' && 
                           style.visibility !== 'hidden' && 
                           style.display !== 'none' &&
                           element.offsetParent !== null;
                """, element)
                
                if not is_clickable:
                    logger.debug(f"元素不可點擊: {element.text.strip()[:20]}")
                    return True
                    
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.debug(f"檢查元素禁用狀態失敗: {e}")
            return False  # 如果檢查失敗，假設元素可用

    def _check_for_disabled_next_button(self, popup_element) -> bool:
        """
        檢查彈出框中是否有禁用的「下一步」或「next」按鈕
        
        Args:
            popup_element: 彈出對話框的 WebElement
            
        Returns:
            True 如果找到禁用的下一步按鈕
        """
        try:
            # 查找包含「下一步」或「next」文字的按鈕
            next_button_patterns = ["下一步", "next", "continue", "繼續", "下一個", "forward"]
            
            for pattern in next_button_patterns:
                try:
                    # 使用 XPath 查找包含特定文字的按鈕
                    xpath = f".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]"
                    buttons = popup_element.find_elements(By.XPATH, xpath)
                    
                    for button in buttons:
                        if button.is_displayed() and self._is_element_disabled(button):
                            logger.info(f"🚫 找到禁用的按鈕: {button.text.strip()}")
                            return True
                            
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"檢查禁用下一步按鈕失敗: {e}")
            return False

    def _extract_form_elements(self, popup_element, form_selectors: list) -> List[Dict[str, str]]:
        """
        從彈出框中提取表單輸入元素
        
        Args:
            popup_element: 彈出對話框的 WebElement
            form_selectors: 表單元素選擇器列表
            
        Returns:
            表單輸入元素列表
        """
        form_elements = []
        
        try:
            for selector in form_selectors:
                try:
                    elements = popup_element.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and not self._is_element_disabled(element):
                            # 獲取元素信息
                            tag_name = element.tag_name.lower()
                            input_type = element.get_attribute("type") or ""
                            name = element.get_attribute("name") or ""
                            value = element.get_attribute("value") or ""
                            placeholder = element.get_attribute("placeholder") or ""
                            
                            # 獲取關聯的 label 文字
                            label_text = self._get_form_element_label(element)
                            
                            # 確定元素類型 - 🎯 優先處理email欄位
                            if input_type == "email" or 'email' in name.lower():
                                element_type = "popup_email"  # 特殊標記email欄位
                            elif input_type == "radio":
                                element_type = "popup_radio"
                            elif input_type == "checkbox":
                                element_type = "popup_checkbox"
                            elif input_type in ["text", "tel", "number"]:
                                element_type = "popup_input"
                            elif tag_name == "select":
                                element_type = "popup_select"
                            elif tag_name == "textarea":
                                element_type = "popup_textarea"
                            else:
                                element_type = "popup_form_element"
                            
                            # 生成描述文字
                            description = label_text or placeholder or value or f"{input_type} 輸入"
                            
                            form_elements.append({
                                'type': element_type,
                                'tag': tag_name,
                                'text': description[:100],
                                'href': "",
                                'title': element.get_attribute("title") or "",
                                'id': element.get_attribute("id") or "",
                                'class': element.get_attribute("class") or "",
                                'onclick': "",
                                'is_popup_element': True,
                                'input_type': input_type,
                                'name': name,
                                'value': value,
                                'placeholder': placeholder
                            })
                            
                except Exception:
                    continue
            
            # 按照頁面順序排序（上到下，左到右）
            if form_elements:
                form_elements.sort(key=lambda elem: (
                    elem.get('position_y', 0), 
                    elem.get('position_x', 0)
                ))
            
            return form_elements
            
        except Exception as e:
            logger.error(f"提取表單元素失敗: {e}")
            return []

    def _get_form_element_label(self, element) -> str:
        """
        獲取表單元素的關聯標籤文字
        
        Args:
            element: 表單元素
            
        Returns:
            標籤文字
        """
        try:
            # 檢查 aria-label
            aria_label = element.get_attribute("aria-label")
            if aria_label:
                return aria_label.strip()
            
            # 檢查關聯的 label 元素
            element_id = element.get_attribute("id")
            if element_id:
                try:
                    label = element.find_element(By.XPATH, f"//label[@for='{element_id}']")
                    if label:
                        return label.text.strip()
                except:
                    pass
            
            # 檢查父元素是否是 label
            try:
                parent = element.find_element(By.XPATH, "..")
                if parent.tag_name.lower() == "label":
                    return parent.text.strip()
            except:
                pass
            
            # 檢查前面的兄弟元素
            try:
                prev_sibling = element.find_element(By.XPATH, "./preceding-sibling::*[1]")
                if prev_sibling.tag_name.lower() in ["label", "span", "div"]:
                    text = prev_sibling.text.strip()
                    if text and len(text) < 50:  # 避免過長的文字
                        return text
            except:
                pass
            
            return ""
            
        except Exception:
            return ""

    def _extract_popup_elements(self, popup_element) -> List[Dict[str, str]]:
        """
        從彈出對話框中提取可點擊元素
        
        Args:
            popup_element: 彈出對話框的 WebElement
            
        Returns:
            彈出對話框內的可點擊元素列表
        """
        if not popup_element:
            return []
            
        try:
            popup_elements = []
            
            # 在彈出對話框內查找可點擊元素
            clickable_selectors = [
                "a", "button", 
                "input[type='submit']", "input[type='button']",
                "[onclick]", "[role='button']",
                ".btn", ".button", ".clickable"
            ]
            
            # 表單輸入元素選擇器
            form_input_selectors = [
                "input[type='radio']",     # 單選按鈕
                "input[type='checkbox']",  # 核取方塊
                "input[type='text']",      # 文字輸入
                "input[type='email']",     # 電子郵件輸入
                "input[type='tel']",       # 電話輸入
                "input[type='number']",    # 數字輸入
                "select",                  # 下拉選單
                "textarea"                 # 文字區域
            ]
            
            logger.info("🔍 提取彈出對話框內的可點擊元素...")
            
            # 🎯 檢測是否有禁用的「下一步」或「next」按鈕
            has_disabled_next_button = self._check_for_disabled_next_button(popup_element)
            
            # 如果有禁用的下一步按鈕，優先處理表單輸入元素
            if has_disabled_next_button:
                logger.info("⚠️  檢測到禁用的「下一步」按鈕，將優先提取表單輸入元素")
                form_elements = self._extract_form_elements(popup_element, form_input_selectors)
                if form_elements:
                    logger.info(f"📝 找到 {len(form_elements)} 個表單輸入元素，將優先顯示")
                    popup_elements.extend(form_elements)
            
            for selector in clickable_selectors:
                try:
                    elements = popup_element.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            # 🚫 檢查元素是否被禁用
                            is_disabled = self._is_element_disabled(element)
                            if is_disabled:
                                logger.info(f"⚠️  跳過禁用的元素: {element.text.strip()[:30]}")
                                continue
                            
                            # 獲取元素信息
                            tag_name = element.tag_name.lower()
                            href = element.get_attribute("href") or ""
                            text = element.text.strip()
                            onclick = element.get_attribute("onclick") or ""
                            role = element.get_attribute("role") or ""
                            
                            # 確定元素類型
                            element_type = "popup_link"
                            if tag_name == "button" or role == "button":
                                element_type = "popup_button"
                            elif tag_name == "input":
                                element_type = "popup_button"
                            elif onclick and not href:
                                element_type = "popup_clickable"
                            
                            # 改進文字提取
                            if not text:
                                text = (element.get_attribute("title") or 
                                       element.get_attribute("alt") or 
                                       element.get_attribute("aria-label") or 
                                       element.get_attribute("value") or 
                                       element.get_attribute("placeholder") or "")
                            
                            # 如果還是沒有文字，根據常見的按鈕類別推測
                            if not text:
                                class_name = element.get_attribute("class") or ""
                                if "close" in class_name.lower():
                                    text = "關閉"
                                elif "cancel" in class_name.lower():
                                    text = "取消"
                                elif "confirm" in class_name.lower() or "ok" in class_name.lower():
                                    text = "確認"
                                elif "submit" in class_name.lower():
                                    text = "提交"
                                else:
                                    text = "彈出框按鈕"
                            
                            # 添加到結果中
                            if text or href or onclick:
                                popup_elements.append({
                                    'type': element_type,
                                    'tag': tag_name,
                                    'text': text[:100] if text else "無文字",
                                    'href': href,
                                    'title': element.get_attribute("title") or "",
                                    'id': element.get_attribute("id") or "",
                                    'class': element.get_attribute("class") or "",
                                    'onclick': onclick,
                                    'is_popup_element': True  # 標記為彈出框元素
                                })
                                
                except Exception:
                    continue
            
            logger.info(f"🎯 在彈出對話框內找到 {len(popup_elements)} 個可點擊元素")
            return popup_elements
            
        except Exception as e:
            logger.error(f"提取彈出對話框元素失敗: {e}")
            return []

    def _extract_visible_elements_with_selenium(self) -> List[Dict[str, str]]:
        """
        使用 Selenium 從當前頁面提取只有可見的可點擊元素（按視覺順序排列）
        優先檢測和處理彈出對話框
        
        Returns:
            可見的可點擊元素列表，按頁面視覺順序排列
        """
        if not self.driver:
            return []
        
        try:
            # 🎯 優先檢測彈出對話框
            popup_element = self._detect_popup_dialog()
            if popup_element:
                logger.info("🚨 檢測到彈出對話框，專注處理對話框內容")
                popup_elements = self._extract_popup_elements(popup_element)
                if popup_elements:
                    return popup_elements
                else:
                    logger.warning("彈出對話框內沒有可點擊元素，回退到主頁面處理")
            
            # 如果沒有彈出對話框或對話框內沒有元素，處理主頁面
            visible_elements = []
            
            # 找到所有可能的可點擊元素（包括圖片連結、按鈕等）
            all_clickable_selectors = [
                "a",  # 所有連結
                "button",  # 所有按鈕
                "input[type='submit']", 
                "input[type='button']",
                "[onclick]",  # 有onclick事件的元素
                "[role='button']",  # 標記為按鈕角色的元素
                ".clickable",  # 常見的可點擊類名
            ]
            
            # 收集所有潛在的可點擊元素
            all_elements = []
            for selector in all_clickable_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_elements.extend(elements)
                except Exception:
                    continue
            
            # 去除重複元素（使用set來去重，但保持順序）
            seen_elements = set()
            unique_elements = []
            for elem in all_elements:
                elem_id = id(elem)
                if elem_id not in seen_elements:
                    seen_elements.add(elem_id)
                    unique_elements.append(elem)
            
            # 按照Y座標（垂直位置）排序，然後按X座標（水平位置）排序
            def get_element_position(element):
                try:
                    location = element.location
                    return (location['y'], location['x'])
                except:
                    return (float('inf'), float('inf'))
            
            unique_elements.sort(key=get_element_position)
            
            # 檢查每個元素是否可見並提取信息
            for element in unique_elements:
                try:
                    # 檢查元素是否顯示且在視窗範圍內
                    if element.is_displayed() and self._is_element_in_viewport(element):
                        # 獲取元素信息
                        tag_name = element.tag_name.lower()
                        href = element.get_attribute("href") or ""
                        text = element.text.strip()
                        onclick = element.get_attribute("onclick") or ""
                        role = element.get_attribute("role") or ""
                        
                        # 確定元素類型
                        element_type = "link"
                        if tag_name == "button" or role == "button":
                            element_type = "button"
                        elif tag_name == "input":
                            element_type = "button"
                        elif onclick and not href:
                            element_type = "clickable"
                        
                        # 改進文字提取：如果沒有直接文字，嘗試從子元素或屬性獲取
                        if not text:
                            # 嘗試從title、alt、aria-label等屬性獲取描述
                            text = (element.get_attribute("title") or 
                                   element.get_attribute("alt") or 
                                   element.get_attribute("aria-label") or 
                                   element.get_attribute("data-title") or "")
                            
                            # 如果還是沒有文字，嘗試從子元素獲取
                            if not text:
                                try:
                                    # 查找子元素中的文字
                                    child_texts = []
                                    child_elements = element.find_elements(By.CSS_SELECTOR, "*")
                                    for child in child_elements[:3]:  # 只檢查前3個子元素避免過多內容
                                        child_text = child.text.strip()
                                        if child_text and len(child_text) < 50:  # 避免過長的文字
                                            child_texts.append(child_text)
                                    if child_texts:
                                        text = " | ".join(child_texts)
                                except:
                                    pass
                        
                        # 如果仍然沒有文字，使用URL中的信息
                        if not text and href:
                            try:
                                from urllib.parse import urlparse
                                parsed = urlparse(href)
                                path_parts = [p for p in parsed.path.split('/') if p]
                                if path_parts:
                                    text = path_parts[-1].replace('_', ' ').replace('-', ' ').title()
                            except:
                                text = "連結"
                        
                        # 只保留有意義的元素
                        if (href and href.startswith(('http://', 'https://', '/'))) or onclick or text:
                            visible_elements.append({
                                'type': element_type,
                                'tag': tag_name,
                                'text': text[:100] if text else "無文字",
                                'href': href,
                                'title': element.get_attribute("title") or "",
                                'id': element.get_attribute("id") or "",
                                'class': element.get_attribute("class") or "",
                                'onclick': onclick,
                            })
                            
                except Exception:
                    continue
            
            logger.info(f"在可見區域找到 {len(visible_elements)} 個可點擊元素（按視覺順序排列）")
            return visible_elements
            
        except Exception as e:
            logger.error(f"提取可見元素失敗: {e}")
            return []
    
    def _is_element_in_viewport(self, element) -> bool:
        """
        檢查元素是否在當前視窗的可見範圍內且容易操作
        更嚴格的可見性檢測，確保用戶真正能看到和操作元素
        
        Args:
            element: Selenium WebElement
            
        Returns:
            元素是否在視窗可見範圍內且容易操作
        """
        try:
            # 獲取元素位置和大小
            location = element.location
            size = element.size
            
            # 獲取視窗信息
            window_height = self.driver.execute_script("return window.innerHeight;")
            window_width = self.driver.execute_script("return window.innerWidth;")
            scroll_top = self.driver.execute_script("return window.pageYOffset;")
            scroll_left = self.driver.execute_script("return window.pageXOffset;")
            
            # 計算元素的邊界位置
            element_top = location['y']
            element_bottom = element_top + size['height']
            element_left = location['x']
            element_right = element_left + size['width']
            
            # 計算可見視窗範圍（更保守的範圍，避免導航區域）
            viewport_top = scroll_top + 120  # 增加頂部緩衝區到120px，避免導航元素
            viewport_bottom = scroll_top + window_height - 80  # 增加底部緩衝區到80px
            viewport_left = scroll_left + 30  # 增加左邊緩衝區
            viewport_right = scroll_left + window_width - 30  # 增加右邊緩衝區
            
            # 檢查元素是否在主要內容區域（排除導航區域）
            visible_height = min(element_bottom, viewport_bottom) - max(element_top, viewport_top)
            visible_width = min(element_right, viewport_right) - max(element_left, viewport_left)
            
            # 確保元素有足夠的可見面積
            if visible_height <= 0 or visible_width <= 0:
                return False
            
            element_area = size['width'] * size['height']
            visible_area = visible_height * visible_width
            
            # 至少80%的元素面積必須可見（更嚴格）
            visibility_ratio = visible_area / max(element_area, 1)
            is_mostly_visible = visibility_ratio >= 0.8
            
            # 更嚴格的大小要求，確保是主要操作元素而非小型導航元素
            has_meaningful_size = size['width'] >= 40 and size['height'] >= 30
            
            # 對於按鈕類型，要求更大的最小尺寸
            element_tag = element.tag_name.lower()
            if element_tag == 'button' or element.get_attribute('type') == 'button':
                has_meaningful_size = size['width'] >= 60 and size['height'] >= 35
            
            # 檢查元素是否在頁面的主要內容區域（而非頂部導航）
            relative_position = (element_top - scroll_top) / window_height
            is_in_main_content = relative_position > 0.15  # 元素必須在頁面15%以下的位置
            
            # 額外檢查：確保元素中心點在主要可見區域
            center_x = element_left + size['width'] // 2
            center_y = element_top + size['height'] // 2
            
            center_in_main_area = (viewport_left <= center_x <= viewport_right and 
                                 viewport_top <= center_y <= viewport_bottom)
            
            result = (is_mostly_visible and 
                     has_meaningful_size and 
                     is_in_main_content and 
                     center_in_main_area)
            
            # 調試信息
            if not result:
                logger.debug(f"元素被過濾: visible_ratio={visibility_ratio:.2f}, "
                           f"size={size['width']}x{size['height']}, "
                           f"in_main_content={is_in_main_content}, "
                           f"relative_pos={relative_position:.2f}")
            
            return result
            
        except Exception as e:
            logger.debug(f"檢查元素可見性失敗: {e}")
            return False

    def _extract_elements_from_current_page(self) -> List[Dict[str, str]]:
        """
        從當前頁面提取可點擊元素（只獲取可見元素）
        
        Returns:
            可見的可點擊元素列表
        """
        if not self.driver:
            return []
        
        try:
            # 使用新的可見元素提取方法
            visible_elements = self._extract_visible_elements_with_selenium()
            
            logger.info(f"在當前頁面的可見區域找到 {len(visible_elements)} 個可點擊元素")
            return visible_elements
            
        except Exception as e:
            logger.error(f"提取當前頁面可見元素失敗: {e}")
            return []
    
    def _persistent_random_click(self, elements: List[Dict[str, str]], wait_time: int) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        """
        在持久瀏覽器中隨機點擊元素
        
        Args:
            elements: 可點擊元素列表
            wait_time: 等待時間
            
        Returns:
            Tuple[點擊的元素資訊, 新頁面的可點擊元素列表]
        """
        if not elements or not self.driver:
            logger.warning("沒有可點擊的元素或瀏覽器未啟動")
            return {}, []
        
        # 過濾掉沒有實際連結或動作的元素（包括彈出框元素和表單元素）
        clickable_elements = [
            elem for elem in elements 
            if (elem.get('href') or elem.get('onclick') or 
                elem['type'] in ['button', 'popup_button', 'popup_link', 'popup_clickable', 
                                'popup_radio', 'popup_checkbox', 'popup_input', 'popup_select', 'popup_textarea'])
        ]
        
        if not clickable_elements:
            logger.warning("沒有有效的可點擊元素")
            return {}, []
        
        # 隨機選擇一個元素
        selected_element = random.choice(clickable_elements)
        logger.info(f"🎯 隨機選擇元素: [{selected_element['type']}] {selected_element['text'][:50]}")
        
        try:
            # 如果元素有 href，直接導航
            if selected_element.get('href') and selected_element['href'].startswith(('http://', 'https://')):
                target_url = selected_element['href']
                logger.info(f"🌐 導航到連結: {target_url}")
                self.driver.get(target_url)
            
            # 如果沒有 href，嘗試在當前頁面找到並點擊元素
            else:
                web_element = self._find_web_element(selected_element)
                
                if web_element:
                    # 滾動到元素位置
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", web_element)
                    time.sleep(1)
                    
                    # 🎯 特殊處理表單元素點擊
                    if selected_element['type'].startswith('popup_'):
                        logger.info(f"📝 點擊表單元素: {selected_element['text'][:30]}")
                        return self._handle_form_element_click(selected_element, web_element, wait_time)
                    else:
                        # 點擊普通元素
                        logger.info(f"🖱️  點擊元素: {selected_element['text'][:30]}")
                        web_element.click()
                else:
                    logger.warning(f"無法找到要點擊的元素: {selected_element['text'][:30]}")
                    return selected_element, []
            
            # 針對彈出框元素，需要更長的等待時間
            if selected_element.get('is_popup_element') or selected_element['type'].startswith('popup_'):
                logger.info("🎯 點擊彈出框元素，等待更長時間讓頁面穩定...")
                time.sleep(4)  # 彈出框關閉後需要更多時間
            else:
                time.sleep(2)
            
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 再次等待確保頁面完全穩定
            time.sleep(1)
            
            # 提取新頁面的可點擊元素
            new_elements = self._extract_elements_from_current_page()
            
            # 如果沒有找到元素，可能是自動滾動功能可以幫助找到更多元素
            if len(new_elements) == 0:
                logger.info("🔄 未找到可點擊元素，嘗試滾動頁面搜尋...")
                # 滾動頁面並重新搜尋
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)
                new_elements = self._extract_elements_from_current_page()
            
            logger.info(f"✅ 點擊成功，在新頁面找到 {len(new_elements)} 個可點擊元素")
            return selected_element, new_elements
            
        except TimeoutException:
            logger.warning("頁面載入超時")
            return selected_element, []
        except (NoSuchElementException, ElementClickInterceptedException) as e:
            logger.warning(f"無法點擊元素: {e}")
            return selected_element, []
        except Exception as e:
            logger.error(f"點擊過程中發生錯誤: {e}")
            return selected_element, []
    
    def continuous_random_navigation(self, start_url: str, max_clicks: int = 5, wait_time: int = 10) -> List[Tuple[Dict[str, str], List[Dict[str, str]]]]:
        """
        連續隨機導航，點擊多個元素（保持瀏覽器視窗開啟）
        
        Args:
            start_url: 起始網頁 URL
            max_clicks: 最大點擊次數
            wait_time: 每次等待時間
            
        Returns:
            每次點擊的結果列表 [(點擊的元素, 新頁面的可點擊元素), ...]
        """
        results = []
        
        if not self.use_selenium:
            logger.warning("連續隨機導航需要使用 Selenium")
            return []
        
        # 啟動瀏覽器並保持開啟
        self.driver = self._setup_driver()
        
        try:
            logger.info(f"開始連續隨機導航，最多點擊 {max_clicks} 次")
            logger.info("🖥️  瀏覽器視窗將保持開啟直到測試完成")
            
            # 載入初始頁面
            logger.info(f"正在載入起始頁面: {start_url}")
            self.driver.get(start_url)
            
            # 等待頁面載入
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)  # 額外等待動態內容
            
            # 獲取初始頁面的可點擊元素
            current_elements = self._extract_elements_from_current_page()
            
            for i in range(max_clicks):
                if not current_elements:
                    logger.info(f"第 {i+1} 次迭代：沒有可用的可點擊元素，停止導航")
                    break
                
                logger.info(f"第 {i+1} 次迭代：當前有 {len(current_elements)} 個可點擊元素")
                
                # 隨機點擊一個元素（使用持久的瀏覽器）
                clicked_element, new_elements = self._persistent_random_click(
                    current_elements, wait_time
                )
                
                if not clicked_element:
                    logger.info(f"第 {i+1} 次迭代：無法點擊任何元素，停止導航")
                    break
                
                results.append((clicked_element, new_elements))
                
                # 更新當前元素列表
                current_elements = new_elements
                
                logger.info(f"第 {i+1} 次迭代完成，點擊了: {clicked_element['text'][:30]}")
                
                # 短暫暫停讓用戶觀察
                time.sleep(1)
            
            logger.info(f"連續導航完成，總共點擊了 {len(results)} 次")
            logger.info("⏳ 瀏覽器將保持開啟 5 秒供觀察...")
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"連續導航過程中發生錯誤: {e}")
        finally:
            # 最後關閉瀏覽器
            if self.driver:
                logger.info("🔒 關閉瀏覽器")
                self.driver.quit()
                self.driver = None
        
        return results

    def __del__(self):
        """清理資源"""
        if self.driver:
            self.driver.quit() 