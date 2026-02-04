import sys
import os
import time
import random
import requests
import threading
from urllib.parse import unquote, urlparse

# ==========================================
# کتابخانه‌های گرافیکی (PySide6)
# ==========================================
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QTextEdit, QTabWidget, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, 
                               QFileDialog, QMenu, QMessageBox, QSplitter, QFrame, QStyleFactory,
                               QAbstractItemView, QSpinBox, QComboBox)
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QSize, QPoint, QEvent, QTimer
from PySide6.QtGui import QIcon, QFont, QCursor, QDesktopServices, QColor, QPalette, QClipboard, QAction, QKeyEvent

# ==========================================
# کتابخانه‌های وب و درایور
# ==========================================
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================================================================
# 1. CORE INJECTION SCRIPT (هسته ثابت V17)
# ============================================================================
NUCLEAR_SCRIPT = r"""
(function() {
    if (window.nova_hooked) return;
    window.nova_hooked = true;
    window.nova_captured = new Set();
    
    console.log("%c>>> NOVA V17 FINAL KERNEL <<<", "color: #00bcd4; font-size: 16px; font-weight: bold;");

    function isValidAudio(url) {
        if (!url || typeof url !== 'string') return false;
        if (url.startsWith('data:') || url.length > 2000) return false;
        if (url.startsWith('blob:') && !url.includes('.mp3')) return false;
        
        const lowerUrl = url.toLowerCase().split('?')[0];
        const validExts = ['.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac', '.wma'];
        const hasExt = validExts.some(ext => lowerUrl.endsWith(ext));
        const hasKeyword = lowerUrl.includes('format=mp3') || lowerUrl.includes('/track/') || lowerUrl.includes('download') || lowerUrl.includes('upload');
        
        return hasExt || hasKeyword;
    }

    function capture(url, source) {
        try {
            if (url && !url.startsWith('http') && !url.startsWith('blob:') && !url.startsWith('data:')) {
                url = new URL(url, window.location.origin).href;
            }
            if (isValidAudio(url)) {
                if (!window.nova_captured.has(url)) {
                    window.nova_captured.add(url);
                }
            }
        } catch(e) {}
    }

    // اسکن دوره‌ای DOM
    window.novaScanDOM = function() {
        document.querySelectorAll('a, link').forEach(el => { if (el.href) capture(el.href, 'DOM_Link'); });
        document.querySelectorAll('audio, video, source').forEach(el => { if (el.src) capture(el.src, 'DOM_Media'); });
        document.querySelectorAll('*').forEach(el => {
            ['data-src', 'data-url', 'data-mp3', 'data-track', 'data-file'].forEach(attr => {
                if (el.hasAttribute(attr)) capture(el.getAttribute(attr), 'DOM_Data');
            });
        });
    };
    setInterval(window.novaScanDOM, 1000);

    // Trap 1: Audio Constructor
    const originalAudio = window.Audio;
    window.Audio = function(src) {
        if (src) capture(src, 'NewAudio');
        const audio = new originalAudio(src);
        audio.addEventListener('play', () => capture(audio.src, 'AudioPlay'));
        audio.addEventListener('loadstart', () => capture(audio.currentSrc, 'AudioLoad'));
        return audio;
    }
    window.Audio.prototype = originalAudio.prototype;

    // Trap 2: CreateElement
    const originalCreateElement = document.createElement;
    document.createElement = function(tagName) {
        const el = originalCreateElement.call(document, tagName);
        if (tagName.toLowerCase() === 'audio' || tagName.toLowerCase() === 'video') {
            el.addEventListener('play', () => capture(el.src, 'ElementPlay'));
            el.addEventListener('loadeddata', () => capture(el.src, 'ElementLoad'));
            new MutationObserver(ms => {
                ms.forEach(m => {
                    if (m.attributeName === 'src') capture(el.src, 'Mutation');
                });
            }).observe(el, {attributes: true});
        }
        return el;
    }
    
    // Trap 3: Fetch API
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const url = args[0] instanceof Request ? args[0].url : args[0];
        if (isValidAudio(url)) capture(url, 'Fetch');
        return originalFetch(...args);
    }
    
    // Trap 4: XHR
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        if (isValidAudio(url)) capture(url, 'XHR');
        return originalOpen.apply(this, arguments);
    }
})();
"""

# ============================================================================
# 2. INTELLIGENT WORKER (THE SWEEPER V2)
# ============================================================================

class SnifferThread(QThread):
    link_found = Signal(str)
    log_signal = Signal(str, str)
    finished_signal = Signal()

    def __init__(self, url, headless=False):
        super().__init__()
        self.url = url
        self.headless = headless
        self.driver = None
        self.is_running = True
        self.processed_links = set()
        # استفاده از ست برای ذخیره مختصات دکمه‌ها جهت جلوگیری از کلیک تکراری
        self.clicked_coordinates = set() 

    def run(self):
        try:
            mode_text = "خودکار هوشمند (Smart Sweeper V2)" if self.headless else "دستی (Manual)"
            self.log_signal.emit(f">>> موتور V17 شروع به کار کرد | حالت: {mode_text}", "#00bcd4")
            
            chrome_options = Options()
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--log-level=3")
            chrome_options.page_load_strategy = 'eager'
            
            if self.headless:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--mute-audio")
                chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
            else:
                chrome_options.add_argument("--start-maximized")
            
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            self.driver.set_page_load_timeout(60)

            # تزریق اولیه
            try: self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': NUCLEAR_SCRIPT})
            except: pass

            self.log_signal.emit(f">>> اتصال به پایگاه: {self.url}", "#ffffff")
            try:
                self.driver.get(self.url)
            except:
                self.log_signal.emit(">>> ادامه پس از لود اولیه...", "orange")

            # تزریق ثانویه
            try: self.driver.execute_script(NUCLEAR_SCRIPT)
            except: pass
            
            # ==============================
            # THE SMART SWEEPER V2 LOGIC
            # ==============================
            if self.headless:
                self.log_signal.emit(">>> شروع اسکن هوشمند...", "#ffeb3b")
                time.sleep(2)
                
                scroll_step = 500
                max_retries = 3
                retry_count = 0
                
                while self.is_running:
                    # 1. اسکن دکمه‌ها در دید فعلی
                    found_in_view = self.scan_and_click_visible_buttons()
                    
                    # 2. بررسی لینک‌ها
                    self.check_captured_links()
                    
                    # 3. اسکرول
                    before_scroll = self.driver.execute_script("return window.pageYOffset;")
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_step});")
                    time.sleep(1)
                    after_scroll = self.driver.execute_script("return window.pageYOffset;")
                    
                    # 4. تشخیص پایان صفحه
                    if after_scroll == before_scroll:
                        retry_count += 1
                        if retry_count >= max_retries:
                            break # پایان صفحه واقعی
                    else:
                        retry_count = 0 # اگر اسکرول شد، ریست کن
                
                self.log_signal.emit(">>> اسکن تمام صفحه تکمیل شد.", "#00e676")
                
            else:
                self.log_signal.emit(">>> مرورگر باز شد. لطفا دستی کلیک کنید...", "#ffeb3b")
            
            # حلقه انتظار نهایی
            while self.is_running:
                if not self.driver.window_handles: break
                self.check_captured_links()
                time.sleep(1)

        except Exception as e:
            if self.is_running:
                self.log_signal.emit(f"!!! خطا: {str(e)}", "#ff5252")
        finally:
            self.cleanup()
            self.finished_signal.emit()

    def scan_and_click_visible_buttons(self):
        """یافتن و کلیک روی دکمه‌ها بدون تکرار"""
        if not self.is_running: return False
        
        selectors = [
            ".play", ".btn-play", ".fa-play", "[class*='play']", "[id*='play']", 
            ".mejs-play button", "button[title*='Play']", ".jp-play", 
            "div[role='button']", "span[class*='icon-play']"
        ]
        
        found_any = False
        action = ActionChains(self.driver)
        
        # جمع‌آوری تمام دکمه‌های کاندید در ویوپورت
        candidates = []
        for sel in selectors:
            elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
            candidates.extend(elems)
            
        for btn in candidates:
            if not self.is_running: break
            try:
                if btn.is_displayed() and btn.size['width'] > 0:
                    # کلید یونیک برای هر دکمه: موقعیت مکانی در صفحه
                    # این باعث می‌شود هر دکمه دقیقاً یک بار کلیک شود
                    loc = btn.location
                    coord_key = f"{loc['x']}-{loc['y']}"
                    
                    if coord_key in self.clicked_coordinates:
                        continue # قبلاً کلیک شده، رد کن
                    
                    self.clicked_coordinates.add(coord_key)
                    found_any = True
                    
                    # اسکرول به دکمه
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn)
                    time.sleep(0.2)
                    
                    # تلاش برای کلیک (اول موس، بعد JS)
                    try:
                        action.move_to_element(btn).pause(0.2).click().perform()
                    except:
                        self.driver.execute_script("arguments[0].click();", btn)
                    
                    self.log_signal.emit(f"--- کلیک روی آیتم جدید...", "#aaa")
                    time.sleep(0.8) # صبر کوتاه برای ارسال درخواست
                    self.check_captured_links()
                    
            except Exception:
                continue
        
        return found_any

    def check_captured_links(self):
        try:
            links = self.driver.execute_script("return Array.from(window.nova_captured || []);")
            if links:
                for link in links:
                    self.process_link(link)
        except: pass

    def process_link(self, link):
        if link not in self.processed_links:
            if "data:" in link or len(link) > 2000 or "base64" in link: return
            if not any(x in link.lower() for x in ['.mp3', '.m4a', '.wav', '.ogg', 'format=mp3', '/track/', 'download']): return
            
            self.processed_links.add(link)
            self.link_found.emit(link)
            self.log_signal.emit(f"+++ شکار شد: {os.path.basename(unquote(link).split('?')[0])}", "#00e676")

    def cleanup(self):
        if self.driver:
            try: self.driver.quit()
            except: pass
        self.driver = None

    def stop(self):
        self.is_running = False

class DownloadWorker(QThread):
    progress = Signal(int, float, str)
    finished = Signal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.is_cancelled = False

    def run(self):
        try:
            folder = os.path.dirname(self.save_path)
            if not os.path.exists(folder): os.makedirs(folder)

            response = requests.get(self.url, stream=True, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
            total_size = int(response.headers.get('content-length', 0))
            
            if response.status_code != 200:
                self.finished.emit("خطا")
                return

            wrote = 0
            start_time = time.time()
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(8192):
                    if self.is_cancelled:
                        self.finished.emit("لغو")
                        return
                    if chunk:
                        wrote += len(chunk)
                        f.write(chunk)
                        elapsed = time.time() - start_time
                        speed = (wrote / 1024) / elapsed if elapsed > 0 else 0
                        percent = (wrote / total_size) * 100 if total_size > 0 else 0
                        self.progress.emit(int(percent), speed, "در حال دانلود...")
            
            self.finished.emit("تکمیل")
        except Exception as e:
            self.finished.emit("خطا")

# ============================================================================
# 3. GUI APPLICATION
# ============================================================================

class NovaMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOVA HUNTER V17 | The Final Edition")
        self.resize(1150, 800)
        self.setup_theme()
        
        self.download_queue = [] 
        self.active_workers = {}
        self.max_concurrent_downloads = 1
        self.sniffer_thread = None
        
        self.setup_ui()
        
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.process_download_queue)
        self.queue_timer.start(1000)

    def closeEvent(self, event):
        self.force_stop_sniffer()
        for w in self.active_workers.values():
            w.is_cancelled = True
            w.wait()
        event.accept()

    def show_notification(self, message, color="#00e676"):
        self.footer_msg.setText(message)
        self.footer_msg.setStyleSheet(f"color: {color}; font-weight: bold;")
        QTimer.singleShot(3000, lambda: self.footer_msg.setText("آماده برای عملیات..."))

    def setup_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QTabWidget::pane { border: 1px solid #333; background: #1e1e1e; }
            QTabBar::tab { background: #252525; color: #aaa; padding: 10px 20px; }
            QTabBar::tab:selected { background: #00bcd4; color: #000; font-weight: bold; }
            QLineEdit, QSpinBox { background: #2c2c2c; border: 1px solid #3e3e3e; padding: 8px; color: #fff; border-radius: 4px; }
            QPushButton { background-color: #00bcd4; color: #000; border-radius: 4px; padding: 8px 15px; font-weight: bold; }
            QPushButton:hover { background-color: #00acc1; }
            QPushButton:disabled { background-color: #555; color: #888; }
            QTableWidget { background-color: #1e1e1e; border: none; gridline-color: #333; color: #fff; }
            QTableWidget::item:selected { background-color: #00bcd4; color: #000; }
            QHeaderView::section { background-color: #252525; padding: 6px; border: none; color: #ccc; }
            QTextEdit { background-color: #151515; border: 1px solid #333; color: #00e676; font-family: 'Consolas'; }
            QProgressBar { border: 1px solid #444; border-radius: 4px; text-align: center; color: #fff; }
            QProgressBar::chunk { background-color: #00bcd4; }
        """)

    def setup_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)

        header = QHBoxLayout()
        title = QLabel("NOVA HUNTER V17")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00bcd4;")
        layout.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.RightToLeft)
        
        self.tab_sniffer = QWidget()
        self.init_sniffer_tab()
        self.tabs.addTab(self.tab_sniffer, "رادار شکار (Sniffer)")
        
        self.tab_download = QWidget()
        self.init_download_tab()
        self.tabs.addTab(self.tab_download, "مدیریت دانلود")
        
        self.tab_batch = QWidget()
        self.init_batch_tab()
        self.tabs.addTab(self.tab_batch, "ایمپورت گروهی")
        
        layout.addWidget(self.tabs)
        
        self.footer_frame = QFrame()
        self.footer_frame.setStyleSheet("background-color: #1a1a1a; border-top: 1px solid #333;")
        footer_layout = QHBoxLayout(self.footer_frame)
        self.footer_msg = QLabel("آماده برای عملیات...")
        self.footer_msg.setStyleSheet("color: #888;")
        footer_layout.addWidget(self.footer_msg)
        layout.addWidget(self.footer_frame)

    # -------------------------- SNIFFER TAB --------------------------
    def init_sniffer_tab(self):
        layout = QVBoxLayout(self.tab_sniffer)
        
        top_bar = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("آدرس سایت موزیک...")
        self.url_input.setLayoutDirection(Qt.LeftToRight)
        
        self.btn_auto = QPushButton("شروع خودکار (AI Sweeper)")
        self.btn_auto.setStyleSheet("background-color: #7b1fa2; color: white;")
        self.btn_auto.clicked.connect(lambda: self.toggle_sniffer(headless=True))
        
        self.btn_manual = QPushButton("شروع دستی (مرورگر)")
        self.btn_manual.clicked.connect(lambda: self.toggle_sniffer(headless=False))
        
        top_bar.addWidget(self.url_input)
        top_bar.addWidget(self.btn_auto)
        top_bar.addWidget(self.btn_manual)
        layout.addLayout(top_bar)
        
        action_bar = QHBoxLayout()
        btn_add_all = QPushButton("افزودن همه به دانلود")
        btn_add_all.setStyleSheet("background-color: #2e7d32; color: white;")
        btn_add_all.clicked.connect(self.add_all_sniffed_to_queue)
        
        btn_save_txt = QPushButton("ذخیره در تکست")
        btn_save_txt.clicked.connect(self.save_sniffed_to_file)
        
        btn_copy_all = QPushButton("کپی همه لینک‌ها")
        btn_copy_all.clicked.connect(self.copy_all_links)
        
        action_bar.addWidget(btn_add_all)
        action_bar.addWidget(btn_save_txt)
        action_bar.addWidget(btn_copy_all)
        action_bar.addStretch()
        layout.addLayout(action_bar)

        splitter = QSplitter(Qt.Vertical)
        self.sniff_table = QTableWidget()
        self.sniff_table.setColumnCount(3)
        self.sniff_table.setHorizontalHeaderLabels(["نام فایل", "لینک", "عملیات"])
        self.sniff_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.sniff_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) 
        self.sniff_table.setLayoutDirection(Qt.RightToLeft)
        
        self.sniff_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sniff_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.sniff_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sniff_table.customContextMenuRequested.connect(self.sniff_table_context_menu)
        self.sniff_table.keyPressEvent = self.sniff_table_key_press
        
        splitter.addWidget(self.sniff_table)
        
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(150)
        splitter.addWidget(self.log_box)
        layout.addWidget(splitter)

    def toggle_sniffer(self, headless):
        # اگر دکمه در حال شروع است
        is_starting = self.btn_auto.text().startswith("شروع") or self.btn_manual.text().startswith("شروع")
        
        if is_starting:
            url = self.url_input.text().strip()
            if not url: 
                self.show_notification("لطفا آدرس سایت را وارد کنید", "red")
                return
            
            # تغییر وضعیت به "توقف"
            self.url_input.setEnabled(False)
            if headless:
                self.btn_auto.setText("توقف عملیات")
                self.btn_auto.setStyleSheet("background-color: #d32f2f; color: white;")
                self.btn_manual.setEnabled(False)
            else:
                self.btn_manual.setText("توقف عملیات")
                self.btn_manual.setStyleSheet("background-color: #d32f2f; color: white;")
                self.btn_auto.setEnabled(False)

            self.sniffer_thread = SnifferThread(url, headless)
            self.sniffer_thread.log_signal.connect(self.append_log)
            self.sniffer_thread.link_found.connect(self.add_sniffed_link)
            self.sniffer_thread.finished_signal.connect(self.reset_sniffer_ui)
            self.sniffer_thread.start()
        
        else:
            # اگر دکمه "توقف" زده شد
            self.force_stop_sniffer()

    def force_stop_sniffer(self):
        if self.sniffer_thread and self.sniffer_thread.isRunning():
            self.append_log(">>> در حال توقف اجباری...", "orange")
            self.sniffer_thread.stop()
            # دیگر منتظر wait نمی مانیم تا UI فریز نشود
            # سیگنال finished_signal به هر حال فراخوانی خواهد شد

    def reset_sniffer_ui(self):
        """بازگردانی دکمه‌ها به حالت اولیه"""
        self.btn_auto.setText("شروع خودکار (AI Sweeper)")
        self.btn_auto.setStyleSheet("background-color: #7b1fa2; color: white;")
        self.btn_auto.setEnabled(True)
        
        self.btn_manual.setText("شروع دستی (مرورگر)")
        self.btn_manual.setStyleSheet("")
        self.btn_manual.setEnabled(True)
        
        self.url_input.setEnabled(True)
        self.show_notification("عملیات متوقف شد / پایان یافت.", "orange")
        self.sniffer_thread = None

    def add_sniffed_link(self, url):
        row = self.sniff_table.rowCount()
        self.sniff_table.insertRow(row)
        filename = os.path.basename(unquote(url).split('?')[0]) or "Unknown.mp3"
        
        self.sniff_table.setItem(row, 0, QTableWidgetItem(filename))
        self.sniff_table.setItem(row, 1, QTableWidgetItem(url))
        
        btn = QPushButton("افزودن")
        btn.setStyleSheet("background-color: #388e3c; color: white; font-size: 11px; padding: 4px;")
        btn.clicked.connect(lambda: self.add_to_download_queue(filename, url))
        self.sniff_table.setCellWidget(row, 2, btn)
        self.sniff_table.scrollToBottom()

    def sniff_table_key_press(self, event):
        if event.key() == Qt.Key_Delete:
            self.delete_selected_rows()
        else:
            QTableWidget.keyPressEvent(self.sniff_table, event)

    def delete_selected_rows(self):
        rows = sorted(set(index.row() for index in self.sniff_table.selectedIndexes()), reverse=True)
        for r in rows:
            self.sniff_table.removeRow(r)
        self.show_notification(f"{len(rows)} آیتم حذف شد.")

    def sniff_table_context_menu(self, pos):
        menu = QMenu()
        copy_link = menu.addAction("کپی لینک")
        add_queue = menu.addAction("افزودن به دانلود")
        delete_item = menu.addAction("حذف (Delete)")
        
        action = menu.exec_(self.sniff_table.mapToGlobal(pos))
        
        if action == delete_item:
            self.delete_selected_rows()
        elif action == add_queue:
            rows = sorted(set(index.row() for index in self.sniff_table.selectedIndexes()))
            for r in rows:
                fname = self.sniff_table.item(r, 0).text()
                url = self.sniff_table.item(r, 1).text()
                self.add_to_download_queue(fname, url)
            self.show_notification(f"{len(rows)} آیتم به صف افزوده شد.")
        elif action == copy_link:
             rows = sorted(set(index.row() for index in self.sniff_table.selectedIndexes()))
             links = [self.sniff_table.item(r, 1).text() for r in rows]
             QApplication.clipboard().setText("\n".join(links))
             self.show_notification("کپی شد.")

    def add_all_sniffed_to_queue(self):
        count = self.sniff_table.rowCount()
        if count == 0: return
        for r in range(count):
            fname = self.sniff_table.item(r, 0).text()
            url = self.sniff_table.item(r, 1).text()
            self.add_to_download_queue(fname, url)
        self.show_notification(f"{count} فایل به صف اضافه شد.")

    def copy_all_links(self):
        count = self.sniff_table.rowCount()
        links = [self.sniff_table.item(r, 1).text() for r in range(count)]
        QApplication.clipboard().setText("\n".join(links))
        self.show_notification("تمامی لینک‌ها کپی شدند.")

    def save_sniffed_to_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "ذخیره", "", "Text Files (*.txt)")
        if path:
            count = self.sniff_table.rowCount()
            with open(path, "w", encoding="utf-8") as f:
                for r in range(count):
                    f.write(self.sniff_table.item(r, 1).text() + "\n")
            self.show_notification("فایل ذخیره شد.")

    def init_download_tab(self):
        layout = QVBoxLayout(self.tab_download)
        
        queue_ctrl = QHBoxLayout()
        queue_ctrl.addWidget(QLabel("تعداد دانلود همزمان:"))
        self.spin_concurrent = QSpinBox()
        self.spin_concurrent.setRange(1, 10)
        self.spin_concurrent.setValue(1)
        self.spin_concurrent.valueChanged.connect(self.update_concurrent_limit)
        queue_ctrl.addWidget(self.spin_concurrent)
        
        btn_start_all = QPushButton("شروع پردازش صف")
        btn_start_all.clicked.connect(self.start_queue_processing)
        queue_ctrl.addWidget(btn_start_all)
        queue_ctrl.addStretch()
        
        layout.addLayout(queue_ctrl)
        
        self.dl_table = QTableWidget()
        self.dl_table.setColumnCount(6)
        self.dl_table.setHorizontalHeaderLabels(["نام فایل", "وضعیت", "پیشرفت", "سرعت", "پوشه مقصد", "عملیات"])
        self.dl_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.dl_table.setLayoutDirection(Qt.RightToLeft)
        layout.addWidget(self.dl_table)

    def update_concurrent_limit(self, val):
        self.max_concurrent_downloads = val

    def add_to_download_queue(self, filename, url, folder_name="Downloads"):
        for r in range(self.dl_table.rowCount()):
            if self.dl_table.item(r, 1).data(Qt.UserRole) == url: return 

        row = self.dl_table.rowCount()
        self.dl_table.insertRow(row)
        
        self.dl_table.setItem(row, 0, QTableWidgetItem(filename))
        
        status_item = QTableWidgetItem("در انتظار")
        status_item.setData(Qt.UserRole, url)
        self.dl_table.setItem(row, 1, status_item)
        
        pbar = QProgressBar()
        pbar.setValue(0)
        self.dl_table.setCellWidget(row, 2, pbar)
        
        self.dl_table.setItem(row, 3, QTableWidgetItem("-"))
        
        btn_folder = QPushButton(folder_name)
        btn_folder.setStyleSheet("text-align: left; padding: 5px; color: #00e676;")
        btn_folder.clicked.connect(lambda: self.change_dest_folder(row))
        self.dl_table.setCellWidget(row, 4, btn_folder)
        
        btn_action = QPushButton("افزودن به صف")
        full_path = os.path.join(os.getcwd(), folder_name, filename)
        btn_action.clicked.connect(lambda: self.queue_single_download(row))
        self.dl_table.setCellWidget(row, 5, btn_action)

    def change_dest_folder(self, row):
        folder = QFileDialog.getExistingDirectory(self, "انتخاب پوشه")
        if folder:
            btn = self.dl_table.cellWidget(row, 4)
            btn.setText(os.path.basename(folder))

    def queue_single_download(self, row):
        if row not in self.download_queue:
            self.download_queue.append(row)
            self.dl_table.item(row, 1).setText("در صف...")
            self.dl_table.cellWidget(row, 5).setText("در صف")
            self.dl_table.cellWidget(row, 5).setEnabled(False)

    def start_queue_processing(self):
        for r in range(self.dl_table.rowCount()):
            status = self.dl_table.item(r, 1).text()
            if status == "در انتظار":
                self.queue_single_download(r)
        self.show_notification("صف دانلود شروع شد.")

    def process_download_queue(self):
        active_count = len(self.active_workers)
        while active_count < self.max_concurrent_downloads and self.download_queue:
            row = self.download_queue.pop(0)
            self.start_download_worker(row)
            active_count += 1

    def start_download_worker(self, row):
        url = self.dl_table.item(row, 1).data(Qt.UserRole)
        filename = self.dl_table.item(row, 0).text()
        folder_name = self.dl_table.cellWidget(row, 4).text()
        if folder_name == "Downloads": folder_name = "Downloads"
        
        save_path = os.path.join(os.getcwd(), folder_name, filename)
        
        worker = DownloadWorker(url, save_path)
        worker.progress.connect(lambda p, s, st: self.update_dl(row, p, s, st))
        worker.finished.connect(lambda st: self.finish_dl(row, st, save_path))
        worker.start()
        
        self.active_workers[row] = worker
        
        btn = self.dl_table.cellWidget(row, 5)
        btn.setText("لغو")
        btn.setEnabled(True)
        btn.setStyleSheet("background-color: #d32f2f;")
        try: btn.clicked.disconnect()
        except: pass
        btn.clicked.connect(lambda: self.cancel_download(row))

    def cancel_download(self, row):
        if row in self.active_workers:
            self.active_workers[row].is_cancelled = True

    def update_dl(self, row, p, s, st):
        self.dl_table.cellWidget(row, 2).setValue(p)
        self.dl_table.item(row, 1).setText(st)
        self.dl_table.item(row, 3).setText(f"{s:.1f} KB/s")

    def finish_dl(self, row, st, path):
        self.dl_table.item(row, 1).setText(st)
        if row in self.active_workers:
            del self.active_workers[row]
            
        btn = self.dl_table.cellWidget(row, 5)
        if st == "تکمیل":
            btn.setText("پوشه")
            btn.setStyleSheet("background-color: #1565c0;")
            try: btn.clicked.disconnect()
            except: pass
            btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path))))
        else:
            btn.setText("تلاش مجدد")
            btn.setStyleSheet("")
            try: btn.clicked.disconnect()
            except: pass
            btn.clicked.connect(lambda: self.queue_single_download(row))

    def init_batch_tab(self):
        layout = QVBoxLayout(self.tab_batch)
        lbl = QLabel("ایمپورت فایل‌های Text (هر فایل = یک پوشه مجزا)")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #00bcd4; margin: 20px;")
        
        btn = QPushButton("انتخاب فایل‌های .txt")
        btn.setMinimumHeight(50)
        btn.clicked.connect(self.process_batch)
        
        self.batch_log = QTextEdit()
        
        layout.addWidget(lbl)
        layout.addWidget(btn)
        layout.addWidget(self.batch_log)

    def process_batch(self):
        files, _ = QFileDialog.getOpenFileNames(self, "انتخاب", "", "Text (*.txt)")
        if not files: return
        
        count = 0
        for path in files:
            folder_name = os.path.splitext(os.path.basename(path))[0].strip()
            target_folder = os.path.join("Downloads", folder_name)
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        link = line.strip()
                        if link.startswith('http'):
                            fname = os.path.basename(unquote(link).split('?')[0])
                            self.add_to_download_queue(fname, link, target_folder)
                            count += 1
                self.batch_log.append(f"فایل {folder_name} پردازش شد.")
            except Exception as e:
                self.batch_log.append(f"خطا: {e}")
        
        self.show_notification(f"{count} لینک اضافه شد.")
        self.tabs.setCurrentIndex(1)

    def append_log(self, msg, color):
        t = time.strftime("%H:%M:%S")
        self.log_box.append(f'<span style="color:#777">[{t}]</span> <span style="color:{color}">{msg}</span>')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("Tahoma", 9)
    app.setFont(font)
    window = NovaMainWindow()
    window.show()
    sys.exit(app.exec())