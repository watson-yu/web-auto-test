#!/usr/bin/env python3
"""
測試引擎中間層
包裝 web_scraper 的複雜功能，提供簡化的 API 給主程式使用
"""

import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from scraper import WebScraper

# 設定日誌
logger = logging.getLogger(__name__)

class TestEngine:
    """
    測試引擎 - 中間層
    包裝 WebScraper 的複雜功能，提供簡化的 API
    """
    
    def __init__(self, headless: bool = True, timeout: int = 10, window_width: int = 640, enable_session_log: bool = True):
        """
        初始化測試引擎
        
        Args:
            headless: 是否無頭模式
            timeout: 默認超時時間
            window_width: 瀏覽器視窗寬度（像素）
            enable_session_log: 是否啟用會話日誌
        """
        self.headless = headless
        self.timeout = timeout
        self.window_width = window_width
        self.enable_session_log = enable_session_log
        self.scraper = WebScraper(use_selenium=True, headless=headless, window_width=window_width)
        self.current_elements = []
        self.test_history = []
        
        # 循環檢測相關
        self.previous_page_elements = []
        self.page_signatures_history = []  # 儲存頁面簽名歷史
        self.clicked_elements_history = []  # 儲存點擊過的元素歷史
        self.url_history = []  # 儲存訪問過的URL歷史
        self.is_loop_detected = False
        self.loop_detection_enabled = True
        
        # 會話日誌相關
        self.session_id = None
        self.session_log = None
        self.session_start_time = None
        
        if self.enable_session_log:
            self._init_session_log()
    
    def _init_session_log(self):
        """初始化會話日誌"""
        try:
            # 創建 logs 目錄
            os.makedirs('logs', exist_ok=True)
            
            # 生成會話 ID（基於時間戳）
            self.session_start_time = datetime.now()
            self.session_id = f"test_{self.session_start_time.strftime('%Y%m%d_%H%M%S')}"
            
            # 初始化會話日誌結構
            self.session_log = {
                "session_id": self.session_id,
                "start_time": self.session_start_time.isoformat(),
                "end_time": None,
                "config": {
                    "headless": self.headless,
                    "timeout": self.timeout,
                    "window_width": self.window_width
                },
                "steps": [],
                "errors": [],
                "summary": {}
            }
            
            logger.info(f"📝 會話日誌已初始化: {self.session_id}")
            
        except Exception as e:
            logger.error(f"❌ 初始化會話日誌失敗: {e}")
            self.enable_session_log = False
    
    def _log_step(self, step_type: str, details: Dict, result: str = "success", error: Optional[str] = None):
        """記錄測試步驟"""
        if not self.enable_session_log or not self.session_log:
            return
        
        step_log = {
            "step": len(self.session_log["steps"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "type": step_type,
            "details": details,
            "result": result,
            "error": error
        }
        
        self.session_log["steps"].append(step_log)
        
        if error:
            self.session_log["errors"].append({
                "step": step_log["step"],
                "timestamp": step_log["timestamp"],
                "error": error
            })
    
    def _save_session_log(self):
        """保存會話日誌到文件（LLM 友好格式）"""
        if not self.enable_session_log or not self.session_log:
            return
        
        try:
            # 更新結束時間和摘要
            end_time = datetime.now().isoformat()
            self.session_log["end_time"] = end_time
            self.session_log["summary"] = {
                "total_steps": len(self.session_log["steps"]),
                "successful_steps": len([s for s in self.session_log["steps"] if s["result"] == "success"]),
                "failed_steps": len([s for s in self.session_log["steps"] if s["result"] == "failed"]),
                "total_errors": len(self.session_log["errors"]),
                "final_elements_count": len(self.current_elements),
                "duration_seconds": (datetime.fromisoformat(end_time) - 
                                   datetime.fromisoformat(self.session_log["start_time"])).total_seconds(),
                "success_rate": len([s for s in self.session_log["steps"] if s["result"] == "success"]) / max(1, len(self.session_log["steps"])),
                "avg_elements_per_page": sum([s["details"].get("new_elements_count", 0) for s in self.session_log["steps"] if s["type"] == "click"]) / max(1, len([s for s in self.session_log["steps"] if s["type"] == "click"]))
            }
            
            # 添加 LLM 分析友好的元數據
            self.session_log["metadata"] = {
                "version": "1.0",
                "tool": "web-auto-test",
                "analysis_ready": True,
                "llm_instructions": "This is an automated web testing session log. Analyze patterns, failures, and performance metrics.",
                "key_metrics": [
                    "duration_seconds",
                    "success_rate", 
                    "total_errors",
                    "avg_elements_per_page"
                ]
            }
            
            # 保存優化的 JSON 格式日誌
            log_file = f"logs/{self.session_id}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_log, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 LLM 分析日誌已保存: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存會話日誌失敗: {e}")
    
    def _save_readable_summary(self, file_path: str):
        """移除此方法 - 不再需要人類可讀格式"""
        pass
    
    def _generate_page_signature(self, elements: List[Dict[str, str]]) -> str:
        """
        生成頁面的唯一簽名，用於檢測循環
        
        Args:
            elements: 頁面上的可點擊元素列表
            
        Returns:
            頁面簽名字符串
        """
        if not elements:
            return "empty_page"
        
        # 創建基於元素類型和文字的簽名
        element_signatures = []
        for element in elements:
            # 使用元素類型和清理後的文字創建簽名
            element_type = element.get('type', 'unknown')
            element_text = element.get('text', '').strip()[:50]  # 限制文字長度避免過長
            href = element.get('href', '').strip()[:100]  # 包含href信息
            
            # 創建元素簽名
            element_sig = f"{element_type}:{element_text}:{href}"
            element_signatures.append(element_sig)
        
        # 排序確保順序一致性（因為有些網站元素順序可能會變化）
        element_signatures.sort()
        
        # 生成頁面簽名
        page_signature = "|".join(element_signatures)
        
        # 使用hash縮短簽名長度
        import hashlib
        signature_hash = hashlib.md5(page_signature.encode('utf-8')).hexdigest()
        
        return signature_hash
    
    def _detect_page_loop(self, current_elements: List[Dict[str, str]]) -> bool:
        """
        檢測是否進入頁面循環
        
        Args:
            current_elements: 當前頁面的可點擊元素列表
            
        Returns:
            True 如果檢測到循環，False 否則
        """
        if not self.loop_detection_enabled:
            return False
        
        # 生成當前頁面簽名
        current_signature = self._generate_page_signature(current_elements)
        
        # 🎯 新增：檢查重複點擊同一元素的情況
        if len(self.clicked_elements_history) >= 3:
            # 檢查最近3次點擊是否都是同一個元素
            recent_clicks = self.clicked_elements_history[-3:]
            if len(set([click.get('text', '') for click in recent_clicks])) == 1:
                repeated_element = recent_clicks[0].get('text', '未知元素')
                logger.warning("🔄 檢測到重複點擊循環！")
                logger.warning(f"   重複點擊元素: {repeated_element}")
                logger.warning(f"   連續重複次數: {len(recent_clicks)}")
                
                self._log_step("loop_detection", {
                    "loop_type": "repeated_clicks",
                    "repeated_element": repeated_element,
                    "repeat_count": len(recent_clicks),
                    "clicked_elements_history": self.clicked_elements_history[-5:]
                }, "detected", f"檢測到重複點擊循環: {repeated_element}")
                
                self.is_loop_detected = True
                return True
        
        # 🎯 檢查頁面簽名循環（原有邏輯）
        if current_signature in self.page_signatures_history:
            first_occurrence = self.page_signatures_history.index(current_signature) + 1
            logger.warning("🔄 檢測到頁面狀態循環！")
            logger.warning(f"   當前頁面簽名: {current_signature}")
            logger.warning(f"   此簽名曾在第 {first_occurrence} 步出現過")
            
            # 記錄循環檢測到會話日誌
            self._log_step("loop_detection", {
                "loop_type": "page_signature",
                "current_signature": current_signature,
                "signature_history": self.page_signatures_history,
                "loop_step": first_occurrence,
                "current_step": len(self.page_signatures_history) + 1,
                "current_elements_count": len(current_elements)
            }, "detected", "檢測到頁面狀態循環")
            
            self.is_loop_detected = True
            return True
        
        # 🎯 檢查相同頁面狀態的重複模式（最近5個簽名中有重複）
        if len(self.page_signatures_history) >= 5:
            recent_signatures = self.page_signatures_history[-5:]
            signature_counts = {}
            for sig in recent_signatures:
                signature_counts[sig] = signature_counts.get(sig, 0) + 1
            
            # 如果最近5個簽名中有任何簽名出現2次以上
            for sig, count in signature_counts.items():
                if count >= 2:
                    logger.warning("🔄 檢測到短期循環模式！")
                    logger.warning(f"   重複簽名: {sig}")
                    logger.warning(f"   在最近5步中出現 {count} 次")
                    
                    self._log_step("loop_detection", {
                        "loop_type": "short_term_pattern",
                        "repeated_signature": sig,
                        "repeat_count": count,
                        "recent_signatures": recent_signatures
                    }, "detected", f"檢測到短期循環模式")
                    
                    self.is_loop_detected = True
                    return True
        
        # 添加當前簽名到歷史記錄
        self.page_signatures_history.append(current_signature)
        
        # 限制歷史記錄長度以避免記憶體問題（保留最近的20個頁面）
        if len(self.page_signatures_history) > 20:
            self.page_signatures_history.pop(0)
        
        logger.debug(f"🔍 頁面簽名已記錄: {current_signature}")
        return False
    
    def get_page_elements(self, url: str) -> List[Dict[str, str]]:
        """
        簡化 API：獲取網頁的所有可點擊元素（優先使用持久瀏覽器的可見元素）
        
        Args:
            url: 網頁 URL
            
        Returns:
            可點擊元素列表，每個元素包含 type, text, href 等資訊
            失敗時返回空列表
        """
        try:
            logger.info(f"🌐 正在分析網頁: {url}")
            
            # 記錄到會話日誌
            if self.session_log:
                self.session_log['config']['url'] = url
            
            # 如果已有持久瀏覽器，使用可見元素檢查
            if hasattr(self.scraper, 'driver') and self.scraper.driver:
                # 導航到指定URL
                self.scraper.driver.get(url)
                
                # 等待頁面載入
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.common.by import By
                import time
                
                WebDriverWait(self.scraper.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(2)  # 額外等待動態內容
                
                # 重置到頁面頂部
                self.scraper.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                # 獲取可見元素
                elements = self.scraper._extract_visible_elements_with_selenium()
                simplified_elements = self._simplify_elements(elements)
                
                # 如果沒有找到可點擊元素，或元素太少，嘗試滾動尋找更多
                if len(simplified_elements) < 3:
                    logger.info(f"🔍 初始視窗僅找到 {len(simplified_elements)} 個可點擊元素，開始滾動搜尋更多...")
                    scrolled_elements = self._scroll_and_find_elements()
                    if scrolled_elements:
                        simplified_elements = scrolled_elements
            else:
                # 回退到傳統方式（但這種情況下應該很少發生）
                elements = self.scraper.get_clickable_elements_from_url(url, self.timeout)
                simplified_elements = self._simplify_elements(elements)
            
            self.current_elements = simplified_elements
            logger.info(f"✅ 找到 {len(simplified_elements)} 個可點擊元素")
            
            # 記錄日誌
            self._log_step("get_elements", {
                "url": url,
                "elements_found": len(simplified_elements),
                "elements_summary": [{"type": e["type"], "text": e["text"][:30]} for e in simplified_elements[:5]]
            })
            
            return simplified_elements
            
        except Exception as e:
            logger.error(f"❌ 獲取頁面元素失敗: {e}")
            self._log_step("get_elements", {"url": url}, "failed", str(e))
            return []
    
    def click_and_navigate(self, element_choice: Optional[int] = None, 
                          start_url: str = "", 
                          keep_browser: bool = True) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
        """
        簡化 API：點擊元素並獲取新頁面的元素
        
        Args:
            element_choice: 要點擊的元素編號（1-based），None 表示隨機選擇
            start_url: 起始 URL（首次使用時需要）
            keep_browser: 是否保持瀏覽器開啟
            
        Returns:
            Tuple[被點擊的元素資訊, 新頁面的可點擊元素列表]
        """
        try:
            # 如果沒有當前元素，先獲取
            if not self.current_elements and start_url:
                self.current_elements = self.get_page_elements(start_url)
            
            if not self.current_elements:
                logger.warning("⚠️  沒有可用的元素可以點擊")
                self._log_step("click", {"element_choice": element_choice}, "failed", "沒有可用的元素")
                return {}, []
            
            # 選擇要點擊的元素
            if element_choice is None:
                # 🎯 最高優先級：如果有email欄位，優先選擇
                email_elements = [elem for elem in self.current_elements 
                                if elem.get('type') in ['popup_email', 'email'] or 
                                   'email' in elem.get('full_element', {}).get('input_type', '').lower() or
                                   'email' in elem.get('full_element', {}).get('name', '').lower()]
                
                if email_elements:
                    selected_element = email_elements[0]  # 選擇第一個email欄位
                    logger.info(f"🎯 最高優先級 - 自動選擇email欄位: {selected_element['text'][:30]}")
                else:
                    # 沒有email欄位時才隨機選擇
                    import random
                    selected_element = random.choice(self.current_elements)
                    logger.info(f"🎲 隨機選擇元素 #{selected_element['id']}")
            else:
                # 用戶指定的選擇
                if 1 <= element_choice <= len(self.current_elements):
                    selected_element = self.current_elements[element_choice - 1]
                    logger.info(f"🎯 用戶選擇元素 #{element_choice}")
                else:
                    error_msg = f"無效的元素編號: {element_choice}"
                    logger.error(f"❌ {error_msg}")
                    self._log_step("click", {"element_choice": element_choice}, "failed", error_msg)
                    return {}, []
            
            logger.info(f"👆 將要點擊: [{selected_element['type']}] {selected_element['text']}")
            
            # 執行點擊操作
            full_elements = [selected_element['full_element']]
            
            if keep_browser and hasattr(self.scraper, 'driver') and self.scraper.driver:
                # 使用持久瀏覽器模式
                clicked_element, new_elements = self.scraper._persistent_random_click(
                    full_elements, self.timeout
                )
                # 簡化新元素
                new_simplified_elements = self._simplify_elements(new_elements)
            else:
                # 使用一次性模式
                clicked_element, new_elements = self.scraper.random_click_and_continue(
                    full_elements, start_url, self.timeout
                )
                new_simplified_elements = self._simplify_elements(new_elements)
            
            # 檢測頁面循環（在更新當前元素之前）
            if self._detect_page_loop(new_simplified_elements):
                logger.warning("⚠️  檢測到頁面循環，停止自動測試")
                logger.info("🔄 可能的原因：")
                logger.info("   - 頁面重新導向到之前訪問過的頁面")
                logger.info("   - 點擊的連結指向當前頁面")
                logger.info("   - 網站導航結構存在循環")
                logger.info("💡 建議：檢查點擊的元素是否為預期的導航路徑")
                
                # 保持瀏覽器開啟供用戶觀察
                if hasattr(self.scraper, 'driver') and self.scraper.driver:
                    logger.info("🔍 瀏覽器視窗將保持開啟，您可以手動檢查頁面狀態")
                
                # 返回點擊的元素和新元素，但標記為循環狀態
                return selected_element, new_simplified_elements
            
            # 更新當前元素列表
            self.current_elements = new_simplified_elements
            
            # 記錄點擊的元素到歷史（用於循環檢測）
            self.clicked_elements_history.append({
                'text': selected_element.get('text', ''),
                'type': selected_element.get('type', ''),
                'href': selected_element.get('href', ''),
                'step': len(self.test_history) + 1,
                'timestamp': __import__('time').strftime("%H:%M:%S")
            })
            
            # 限制點擊歷史長度（保留最近的10次）
            if len(self.clicked_elements_history) > 10:
                self.clicked_elements_history.pop(0)
            
            # 記錄測試歷史
            self.test_history.append({
                'step': len(self.test_history) + 1,
                'clicked_element': selected_element,
                'result_count': len(new_simplified_elements),
                'timestamp': __import__('time').strftime("%H:%M:%S"),
                'page_signature': self.page_signatures_history[-1] if self.page_signatures_history else "unknown"
            })
            
            # 記錄會話日誌
            if clicked_element:
                self._log_step("click", {
                    "clicked_element": selected_element,
                    "new_elements_count": len(new_simplified_elements),
                    "element_choice": element_choice,
                    "choice_method": "random" if element_choice is None else "manual",
                    "page_signature": self.page_signatures_history[-1] if self.page_signatures_history else "unknown"
                })
                logger.info(f"✅ 點擊成功，新頁面有 {len(new_simplified_elements)} 個可點擊元素")
            else:
                self._log_step("click", {
                    "clicked_element": selected_element,
                    "element_choice": element_choice
                }, "failed", "點擊操作失敗")
            
            return selected_element, new_simplified_elements
            
        except Exception as e:
            logger.error(f"❌ 點擊操作失敗: {e}")
            self._log_step("click", {"element_choice": element_choice}, "failed", str(e))
            return {}, []
    
    def _simplify_elements(self, elements: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """簡化元素資訊（使用較寬鬆的過濾條件以包含圖片連結）"""
        simplified = []
        for element in elements:
            # 更寬鬆的過濾條件：
            # 1. 有 href 屬性的連結
            # 2. 有 onclick 事件的元素
            # 3. button 類型的元素
            # 4. 有描述性文字的連結（即使沒有 href）
            is_valid = False
            
            if element.get('href'):
                # 任何有 href 的元素都保留（包括相對路徑和錨點）
                is_valid = True
            elif element.get('onclick'):
                # 有 onclick 事件的元素
                is_valid = True
            elif element['type'] == 'button':
                # 按鈕類型
                is_valid = True
            elif element.get('text', '').strip():
                # 有描述性文字的元素（可能是圖片連結）
                text = element.get('text', '').strip()
                # 過濾掉太短或太長的文字
                if 2 <= len(text) <= 50:
                    is_valid = True
            
            if is_valid:
                simplified.append({
                    'id': len(simplified) + 1,
                    'type': element['type'],
                    'text': element['text'][:100] if element.get('text') else '無文字',
                    'href': element.get('href', ''),
                    'element_id': element.get('id', ''),
                    'css_class': element.get('class', ''),
                    'full_element': element
                })
        
        logger.info(f"🔍 從 {len(elements)} 個原始元素中篩選出 {len(simplified)} 個有效元素")
        return simplified
    
    def _scroll_and_find_elements(self, max_scrolls: int = 3) -> List[Dict[str, str]]:
        """
        當沒有找到可點擊元素時，向下滾動並重新檢測
        
        Args:
            max_scrolls: 最大滾動次數
            
        Returns:
            找到的可點擊元素列表
        """
        if not hasattr(self.scraper, 'driver') or not self.scraper.driver:
            return []
        
        all_elements = []
        
        for scroll_count in range(max_scrolls):
            logger.info(f"📜 第 {scroll_count + 1} 次滾動搜尋可點擊元素...")
            
            # 向下滾動一個視窗高度
            self.scraper.driver.execute_script("window.scrollBy(0, window.innerHeight);")
            
            # 等待滾動完成和內容載入
            import time
            time.sleep(1)
            
            # 檢測當前可見區域的元素
            visible_elements = self.scraper._extract_visible_elements_with_selenium()
            simplified_elements = self._simplify_elements(visible_elements)
            
            if simplified_elements:
                logger.info(f"✅ 滾動後找到 {len(simplified_elements)} 個可點擊元素")
                return simplified_elements
            
            logger.info(f"⏭️  第 {scroll_count + 1} 次滾動未找到可點擊元素，繼續滾動...")
        
        logger.warning(f"⚠️  滾動 {max_scrolls} 次後仍未找到可點擊元素")
        return []
    
    def start_persistent_browser(self, url: str) -> bool:
        """
        啟動持久瀏覽器會話
        
        Args:
            url: 起始網頁 URL
            
        Returns:
            是否成功啟動
        """
        try:
            logger.info("🚀 啟動持久瀏覽器會話")
            
            # 記錄到會話日誌配置
            if self.session_log:
                self.session_log['config']['url'] = url
            
            # 設置瀏覽器
            self.scraper.driver = self.scraper._setup_driver()
            
            # 載入起始頁面
            logger.info(f"🌐 載入起始頁面: {url}")
            self.scraper.driver.get(url)
            
            # 等待頁面載入完成
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            import time
            
            WebDriverWait(self.scraper.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)  # 額外等待動態內容載入
            
            # 獲取初始可見元素
            initial_elements = self.scraper._extract_visible_elements_with_selenium()
            self.current_elements = self._simplify_elements(initial_elements)
            
            # 檢查是否需要滾動：
            # 1. 元素太少（少於3個）
            # 2. 或者元素看起來都是導航/UI元素（沒有實質內容）
            needs_scrolling = len(self.current_elements) < 3
            
            if not needs_scrolling and self.current_elements:
                # 檢查是否主要是導航元素
                nav_keywords = ['搜尋', '找專家', '找接案', '登入', '註冊', '首頁', '關於', '聯絡']
                nav_element_count = sum(1 for elem in self.current_elements 
                                      if any(keyword in elem.get('text', '') for keyword in nav_keywords))
                
                # 如果超過一半的元素是導航元素，則需要滾動找更多內容
                if nav_element_count >= len(self.current_elements) * 0.6:
                    needs_scrolling = True
                    logger.info(f"🔍 檢測到 {nav_element_count}/{len(self.current_elements)} 個導航元素，滾動尋找主要內容...")
            
            if needs_scrolling:
                if len(self.current_elements) == 0:
                    logger.info("🔍 初始視窗未找到可點擊元素，開始滾動搜尋...")
                else:
                    logger.info(f"🔍 初始視窗僅找到 {len(self.current_elements)} 個元素，滾動尋找更多主要內容...")
                
                scrolled_elements = self._scroll_and_find_elements()
                if scrolled_elements:
                    self.current_elements = scrolled_elements
            
            logger.info(f"✅ 瀏覽器已啟動，找到 {len(self.current_elements)} 個可點擊元素")
            
            # 記錄日誌
            self._log_step("start_browser", {
                "url": url,
                "window_width": self.window_width,
                "initial_elements_count": len(self.current_elements)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 啟動持久瀏覽器失敗: {e}")
            self._log_step("start_browser", {"url": url}, "failed", str(e))
            return False
    
    def close_browser(self):
        """關閉瀏覽器"""
        try:
            if hasattr(self.scraper, 'driver') and self.scraper.driver:
                logger.info("🔒 關閉瀏覽器")
                self.scraper.driver.quit()
                self.scraper.driver = None
                
                # 記錄日誌並保存會話
                self._log_step("close_browser", {
                    "final_elements_count": len(self.current_elements)
                })
                
                # 保存會話日誌
                self._save_session_log()
                
        except Exception as e:
            logger.error(f"關閉瀏覽器時出錯: {e}")
            self._log_step("close_browser", {}, "failed", str(e))
            # 即使出錯也要嘗試保存日誌
            self._save_session_log()
    
    def get_test_summary(self) -> Dict:
        """獲取測試摘要"""
        return {
            'total_steps': len(self.test_history),
            'current_elements': len(self.current_elements),
            'history': self.test_history,
            'headless_mode': self.headless
        }
    
    def print_current_elements(self, max_display: int = 10):
        """顯示當前可點擊元素"""
        if not self.current_elements:
            print("📋 當前沒有可點擊的元素")
            return
        
        print(f"\n📋 當前頁面的可點擊元素 (共 {len(self.current_elements)} 個):")
        print("=" * 80)
        
        for i, element in enumerate(self.current_elements[:max_display], 1):
            print(f"{i:2d}. [{element['type'].upper():6}] {element['text']}")
            if element['href']:
                print(f"     🔗 {element['href']}")
        
        if len(self.current_elements) > max_display:
            print(f"     ... 還有 {len(self.current_elements) - max_display} 個元素")
        print()
    
    def disable_loop_detection(self):
        """停用循環檢測功能"""
        self.loop_detection_enabled = False
        logger.info("🔄 循環檢測已停用")
    
    def enable_loop_detection(self):
        """啟用循環檢測功能"""
        self.loop_detection_enabled = True
        logger.info("🔄 循環檢測已啟用")
    
    def reset_loop_detection(self):
        """重置循環檢測狀態"""
        self.is_loop_detected = False
        self.page_signatures_history = []
        self.clicked_elements_history = []
        self.url_history = []
        logger.info("🔄 循環檢測狀態已重置")
    
    def get_loop_detection_status(self) -> Dict:
        """獲取循環檢測狀態資訊"""
        recent_clicks = [click.get('text', '') for click in self.clicked_elements_history[-5:]]
        return {
            "enabled": self.loop_detection_enabled,
            "loop_detected": self.is_loop_detected,
            "pages_visited": len(self.page_signatures_history),
            "page_signatures": self.page_signatures_history[-5:] if self.page_signatures_history else [],  # 顯示最近5個簽名
            "unique_pages": len(set(self.page_signatures_history)),
            "clicked_elements_count": len(self.clicked_elements_history),
            "recent_clicks": recent_clicks,  # 最近5次點擊的元素文字
            "repeated_clicks": len(recent_clicks) - len(set(recent_clicks)) if recent_clicks else 0  # 重複點擊次數
        }
    
    def __del__(self):
        """清理資源"""
        self.close_browser() 