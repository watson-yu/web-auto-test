#!/usr/bin/env python3
"""
網頁自動測試工具 - 主程式
簡化版的測試流程，提供三種測試模式
"""
import os
from typing import Optional
from engine import TestEngine
import time

# 載入環境變數
try:
    from dotenv import load_dotenv
    load_dotenv()  # 載入 .env 文件
    print("📝 已載入 .env 配置文件")
except ImportError:
    print("⚠️  未安裝 python-dotenv，使用預設配置")
except Exception:
    print("⚠️  未找到 .env 文件，使用預設配置")

# 從環境變數讀取配置，如果沒有則使用預設值
def get_env_bool(key: str, default: bool) -> bool:
    """從環境變數獲取布林值"""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')

def get_env_int(key: str, default: int) -> int:
    """從環境變數獲取整數值"""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default

# 配置變數（從 .env 文件或使用預設值）
DEFAULT_TEST_URL = os.getenv('DEFAULT_TEST_URL', 'https://httpbin.org/html')
WINDOW_WIDTH = get_env_int('WINDOW_WIDTH', 480)
ENABLE_LOGS = get_env_bool('ENABLE_LOGS', True)
TIMEOUT = get_env_int('TIMEOUT', 10)
HEADLESS_MODE = get_env_bool('HEADLESS_MODE', False)

def basic_test_flow():
    """
    基本自動測試流程 - 隨機點擊元素
    修改這個函數來調整你的測試邏輯
    """
    # 測試設定
    test_url = DEFAULT_TEST_URL  # 可以修改測試網站
    headless = HEADLESS_MODE  # 設定為 False 顯示瀏覽器
    max_clicks = 3    # 最大點擊次數
    window_width = WINDOW_WIDTH  # 瀏覽器視窗寬度（像素），可以修改為任何寬度
    enable_logs = ENABLE_LOGS  # 是否啟用會話日誌
    
    print("🎯 開始網頁自動測試")
    print(f"📍 測試網站: {test_url}")
    print(f"🎲 測試模式: {'無頭模式' if headless else '有頭模式（顯示瀏覽器）'}")
    print(f"🎯 最大點擊次數: {max_clicks}")
    print(f"📱 視窗大小: {window_width}px × 全螢幕高度")
    print(f"📝 會話日誌: {'啟用' if enable_logs else '停用'}")
    
    # 初始化測試引擎
    engine = TestEngine(headless=headless, timeout=TIMEOUT, window_width=window_width, enable_session_log=enable_logs)
    
    try:
        # 啟動瀏覽器並獲取起始頁面元素
        if not engine.start_persistent_browser(test_url):
            print("❌ 無法啟動瀏覽器，測試結束")
            return
        
        print(f"✅ 瀏覽器已啟動，視窗大小已設定為 {window_width}px 寬度")
        
        # 執行隨機點擊測試
        for step in range(1, max_clicks + 1):
            print(f"\n🎲 第 {step} 步")
            
            # 隨機點擊並獲取新元素
            clicked_element, new_elements = engine.click_and_navigate()
            
            if not clicked_element:
                print("⚠️  沒有可點擊的元素，測試結束")
                break
            
            print(f"✅ 點擊成功: [{clicked_element['type']}] {clicked_element['text']}")
            print(f"📊 新頁面找到 {len(new_elements)} 個可點擊元素")
            
            # 檢查是否檢測到循環
            if engine.is_loop_detected:
                print("\n🔄 檢測到頁面循環！")
                print("📋 循環檢測詳情：")
                print(f"   • 在第 {step} 步檢測到與之前頁面相同的可點擊元素")
                print(f"   • 目前共記錄了 {len(engine.page_signatures_history)} 個不同的頁面簽名")
                print(f"   • 最後點擊的元素: {clicked_element['text'][:50]}")
                print("\n⏹️  為避免無限循環，自動測試已停止")
                print("🔍 瀏覽器視窗將保持開啟供您檢查當前狀態")
                break
            
            # 短暫暫停讓瀏覽器載入
            time.sleep(2)
        
        if not engine.is_loop_detected:
            print(f"\n🎉 自動測試完成！總共點擊了 {min(step, max_clicks)} 次")
        else:
            print(f"\n🛑 測試因循環檢測而提前結束，已執行 {step} 步")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
    finally:
        print("\n⏰ 瀏覽器將保持開啟 10 秒供觀察...")
        time.sleep(10)
        engine.close_browser()
        
        # 提示用戶查看日誌
        if enable_logs and engine.session_id:
            print(f"\n📄 LLM 分析日誌已保存:")
            print(f"   📊 logs/{engine.session_id}.json")

def interactive_test_flow():
    """
    互動式測試流程 - 讓用戶手動選擇要點擊的元素
    """
    # 測試設定
    window_width = WINDOW_WIDTH  # 瀏覽器視窗寬度（像素），可以修改
    enable_logs = ENABLE_LOGS  # 是否啟用會話日誌
    
    test_url = input("請輸入測試網站 URL (直接按 Enter 使用預設): ").strip()
    if not test_url:
        test_url = DEFAULT_TEST_URL
    
    print(f"\n🎯 開始互動式測試")
    print(f"📍 測試網站: {test_url}")
    print(f"📐 視窗寬度: {window_width}px")
    print(f"📝 會話日誌: {'啟用' if enable_logs else '停用'}")
    
    # 初始化測試引擎（有頭模式）
    engine = TestEngine(headless=False, timeout=TIMEOUT, window_width=window_width, enable_session_log=enable_logs)
    
    try:
        # 啟動瀏覽器
        if not engine.start_persistent_browser(test_url):
            print("❌ 瀏覽器啟動失敗")
            return
        
        step = 1
        while True:
            print(f"\n🔄 第 {step} 步")
            engine.print_current_elements()
            
            if not engine.current_elements:
                print("⚠️  沒有可點擊的元素，測試結束")
                break
            
            # 讓用戶選擇
            try:
                choice = input("\n請選擇要點擊的元素編號 (按 Enter 隨機選擇，輸入 'q' 退出): ").strip()
                
                if choice.lower() == 'q':
                    print("👋 用戶退出測試")
                    break
                
                element_choice = int(choice) if choice.isdigit() else None
                
                # 執行點擊
                clicked_element, new_elements = engine.click_and_navigate(
                    element_choice=element_choice,
                    keep_browser=True
                )
                
                if clicked_element:
                    print(f"✅ 成功點擊: {clicked_element['text'][:50]}")
                    
                    # 檢查是否檢測到循環
                    if engine.is_loop_detected:
                        print("\n🔄 循環警告！")
                        print("📋 檢測到與之前訪問過的頁面相同的可點擊元素")
                        print(f"📊 頁面簽名歷史記錄: {len(engine.page_signatures_history)} 個不同頁面")
                        
                        user_choice = input("\n請選擇操作 (c=繼續測試, s=停止測試): ").strip().lower()
                        if user_choice == 's':
                            print("🛑 用戶選擇停止測試")
                            break
                        else:
                            print("⚠️  繼續測試（請注意可能的循環）")
                            # 重置循環檢測標誌讓測試可以繼續
                            engine.is_loop_detected = False
                    
                    step += 1
                else:
                    print("❌ 點擊失敗")
                    break
                    
            except ValueError:
                print("❌ 請輸入有效的數字")
            except KeyboardInterrupt:
                print("\n⚠️  用戶中斷測試")
                break
    
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
    finally:
        print("\n⏰ 瀏覽器將保持開啟 8 秒供觀察...")
        time.sleep(8)
        engine.close_browser()
        print("✅ 測試完成")
        
        # 提示用戶查看日誌
        if enable_logs and engine.session_id:
            print(f"\n📄 LLM 分析日誌已保存:")
            print(f"   📊 logs/{engine.session_id}.json")

def custom_test_example():
    """
    自定義測試範例 - 展示如何建立自己的測試邏輯
    """
    # 測試設定
    window_width = 800  # 可以為不同的測試設定不同的寬度
    enable_logs = ENABLE_LOGS  # 是否啟用會話日誌
    
    print("🎯 自定義測試範例：尋找特定類型的元素")
    print(f"📐 視窗寬度: {window_width}px")
    print(f"📝 會話日誌: {'啟用' if enable_logs else '停用'}")
    
    engine = TestEngine(headless=False, timeout=TIMEOUT, window_width=window_width, enable_session_log=enable_logs)
    
    try:
        # 啟動瀏覽器
        if not engine.start_persistent_browser("https://httpbin.org/links/10"):
            return
        
        # 尋找連結類型的元素
        link_count = 0
        for element in engine.current_elements:
            if element['type'] == 'link' and element['href']:
                print(f"🔗 找到連結: {element['text'][:30]} -> {element['href']}")
                link_count += 1
        
        print(f"\n📊 總共找到 {link_count} 個連結")
        
        # 只點擊連結類型的元素
        if link_count > 0:
            print("\n🎯 隨機點擊一個連結...")
            
            # 過濾出只有連結的元素
            links = [i for i, elem in enumerate(engine.current_elements, 1) 
                    if elem['type'] == 'link' and elem['href']]
            
            if links:
                import random
                selected_link = random.choice(links)
                clicked_element, new_elements = engine.click_and_navigate(
                    element_choice=selected_link,
                    keep_browser=True
                )
                
                if clicked_element:
                    print(f"✅ 成功點擊連結: {clicked_element['text'][:50]}")
                    print(f"📊 新頁面有 {len(new_elements)} 個元素")
        
        time.sleep(3)  # 測試過程中的短暫觀察
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
    finally:
        print("\n⏰ 瀏覽器將保持開啟 12 秒供觀察...")
        time.sleep(12)
        engine.close_browser()
        
        # 提示用戶查看日誌
        if enable_logs and engine.session_id:
            print(f"\n📄 LLM 分析日誌已保存:")
            print(f"   📊 logs/{engine.session_id}.json")

def main():
    """主選單"""
    print("🚀 網頁自動測試工具 - 簡化版")
    print("=" * 50)
    
    while True:
        print("\n請選擇測試模式:")
        print("1. 基本自動測試 (隨機點擊)")
        print("2. 互動式測試 (手動選擇)")
        print("3. 自定義測試範例")
        print("4. 退出")
        
        choice = input("\n請輸入選項 (1-4): ").strip()
        
        if choice == '1':
            basic_test_flow()
        elif choice == '2':
            interactive_test_flow()
        elif choice == '3':
            custom_test_example()
        elif choice == '4':
            print("👋 再見！")
            break
        else:
            print("❌ 無效選項，請重新選擇")

if __name__ == '__main__':
    main() 