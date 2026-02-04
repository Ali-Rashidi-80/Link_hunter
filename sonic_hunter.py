import flet as ft
import time
import os
import threading
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
#  SONIC HUNTER V8: BUG-FREE EDITION
# ==========================================

class AudioHooker:
    def __init__(self, url, log_callback):
        self.url = url
        self.log = log_callback
        self.captured_links = set()
        self.driver = None
        self.is_listening = True

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized") 
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-site-isolation-trials")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.log(">>> [INIT] باز کردن مرورگر در حالت شنود...")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def inject_traps(self):
        """تزریق کدهای جاسوسی به هسته مرورگر (با فرمت صحیح Raw String)"""
        # استفاده از r""" برای جلوگیری از SyntaxWarning
        trap_script = r"""
        window.captured_audio = [];
        
        // 1. تله‌گذاری روی تگ Audio (استاندارد)
        const originalAudio = window.Audio;
        window.Audio = function(src) {
            const audio = new originalAudio(src);
            if (src) window.captured_audio.push(src);
            
            audio.addEventListener('play', function() {
                if(this.src) window.captured_audio.push(this.src);
            });
            audio.addEventListener('loadstart', function() {
                if(this.currentSrc) window.captured_audio.push(this.currentSrc);
            });
            return audio;
        }

        // 2. تله‌گذاری روی ساخت المنت (Dynamic Elements)
        const originalCreateElement = document.createElement;
        document.createElement = function(tagName) {
            const el = originalCreateElement.call(document, tagName);
            if (tagName.toLowerCase() === 'audio') {
                el.addEventListener('play', function() {
                    if(this.src) window.captured_audio.push(this.src);
                });
                // بررسی تغییرات src
                new MutationObserver((mutations) => {
                    mutations.forEach((m) => {
                        if (m.attributeName === 'src' && el.src) {
                            window.captured_audio.push(el.src);
                        }
                    });
                }).observe(el, {attributes: true});
            }
            return el;
        };

        // 3. تله‌گذاری روی شبکه (Fetch/XHR) برای فایل‌های MP3
        const originalFetch = window.fetch;
        window.fetch = async function(...args) {
            const url = args[0] ? args[0].toString() : '';
            // رجکس ساده برای یافتن فایل صوتی
            if (url.match(/\.(mp3|m4a|wav|ogg)/i)) {
                window.captured_audio.push(url);
            }
            return originalFetch(...args);
        };
        """
        try:
            self.driver.execute_script(trap_script)
            self.log(">>> [TRAP] تله‌های صوتی با موفقیت فعال شدند.")
        except Exception as e:
            self.log(f"!!! خطا در تزریق: {e}")

    def auto_click_play_buttons(self):
        """تلاش برای کلیک خودکار روی دکمه‌های Play"""
        self.log(">>> [AUTO-CLICK] جستجو و کلیک روی دکمه‌های پخش...")
        script = r"""
        // پیدا کردن دکمه‌هایی که شبیه Play هستند
        let buttons = document.querySelectorAll('.fa-play, .dashicons-play, .play-icon, [aria-label="Play"], .mejs-play');
        if (buttons.length === 0) {
            // جستجوی عمیق‌تر برای دکمه‌های خاص سایت آهنگ پلاس
            buttons = document.querySelectorAll('div[class*="play"], span[class*="play"], i[class*="play"]');
        }
        
        let count = 0;
        buttons.forEach((btn, index) => {
            // فقط دکمه‌های visible
            if(btn.offsetParent !== null) {
                setTimeout(() => {
                    try { btn.click(); } catch(e) {}
                }, index * 2000); // هر 2 ثانیه یکی
                count++;
            }
        });
        return count;
        """
        try:
            count = self.driver.execute_script(script)
            self.log(f"--- تلاش برای کلیک روی {count} دکمه مشکوک...")
        except:
            pass

    def run(self):
        try:
            self.driver = self.setup_driver()
            self.driver.get(self.url)
            time.sleep(5) 
            
            # فعال‌سازی تله‌ها
            self.inject_traps()
            
            self.log(">>> [WAIT] لطفا صبر کنید یا دستی روی دکمه‌های Play کلیک کنید...")
            
            # تلاش خودکار برای کلیک
            threading.Thread(target=self.auto_click_play_buttons).start()

            # حلقه شنود (Polling)
            start_time = time.time()
            while self.is_listening:
                try:
                    # دریافت لیست از متغیر جاوااسکریپت ما
                    new_links = self.driver.execute_script("return window.captured_audio;")
                    if new_links:
                        for link in new_links:
                            if link and "blob:" not in link and link not in self.captured_links:
                                # تمیزکاری لینک
                                clean = link.replace('http://localhost', '').strip()
                                if clean.startswith('//'): clean = 'https:' + clean
                                if not clean.startswith('http'): 
                                    from urllib.parse import urljoin
                                    clean = urljoin(self.url, clean)
                                
                                self.captured_links.add(clean)
                                self.log(f"+++ شکار شد: {clean.split('/')[-1]}")
                except:
                    pass
                
                time.sleep(1.5)

        except Exception as e:
            self.log(f"!!! خطا: {str(e)}")
        finally:
            self.log(">>> پایان عملیات شنود.")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            return list(self.captured_links)

    def stop(self):
        self.is_listening = False

# --- GUI ---
def main(page: ft.Page):
    page.title = "Sonic Hunter V8 - Bug Free"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 500
    page.window_height = 800
    page.padding = 20
    
    C_MAIN = ft.Colors.PINK_ACCENT 
    C_TEXT = ft.Colors.WHITE

    header = ft.Column([
        ft.Text("SONIC HUNTER V8", size=28, weight=ft.FontWeight.BOLD, color=C_MAIN),
        ft.Text("روش شکار لحظه‌ای (Audio Hook)", size=12, color=ft.Colors.GREY_400),
        ft.Text("نسخه بدون ارور - با اطمینان اجرا کنید", size=11, color=ft.Colors.GREEN_ACCENT),
    ])

    url_input = ft.TextField(
        label="آدرس سایت",
        value="https://ahangplus.gamangroup.ir/%D8%A2%D9%87%D9%86%DA%AF-%D8%A8%DB%8C-%DA%A9%D9%84%D8%A7%D9%85-%D9%85%D8%AD%D9%84-%DA%A9%D8%A7%D8%B1/",
        text_size=12,
        # تغییر آیکون به چیزی که مطمئنیم وجود دارد
        prefix_icon=ft.Icons.SEARCH, 
        border_color=C_MAIN
    )

    log_list = ft.ListView(expand=True, spacing=5, auto_scroll=True)
    log_box = ft.Container(
        content=log_list,
        bgcolor=ft.Colors.BLACK45,
        border=ft.border.all(1, C_MAIN),
        border_radius=10,
        padding=10,
        height=350
    )

    found_count = ft.Text("0", size=40, weight=ft.FontWeight.BOLD, color=C_MAIN)

    def add_log(msg):
        c = C_TEXT
        if ">>>" in msg: c = ft.Colors.CYAN_200
        if "+++" in msg: c = ft.Colors.GREEN_ACCENT
        if "!!!" in msg: c = ft.Colors.RED_ACCENT
        log_list.controls.append(ft.Text(msg, color=c, font_family="Consolas", size=12))
        page.update()

    def save_results(links):
        if not links: return
        with open("hooked_music.txt", "w", encoding="utf-8") as f:
            f.write(f"Source: {url_input.value}\n{'='*50}\n")
            for l in links: f.write(f"{l}\n")
        
        try: os.startfile("hooked_music.txt")
        except: pass

    # متغیر گلوبال برای کنترلر
    extractor = None

    def start_click(e):
        if not url_input.value: return
        
        btn_start.disabled = True
        btn_stop.disabled = False
        log_list.controls.clear()
        found_count.value = "0"
        page.update()

        def worker():
            nonlocal extractor
            extractor = AudioHooker(url_input.value, add_log)
            results = extractor.run()
            
            found_count.value = str(len(results))
            if results:
                save_results(results)
                add_log(f">>> {len(results)} فایل ذخیره شد.")
            else:
                add_log("!!! فایلی پیدا نشد. آیا دکمه پخش زده شد؟")

            btn_start.disabled = False
            btn_stop.disabled = True
            page.update()

        threading.Thread(target=worker, daemon=True).start()

    def stop_click(e):
        if extractor:
            add_log(">>> دستور توقف ارسال شد...")
            extractor.stop()

    btn_start = ft.ElevatedButton("شروع شکار (مرورگر باز می‌شود)", on_click=start_click, bgcolor=C_MAIN, color=ft.Colors.BLACK, icon=ft.Icons.PLAY_ARROW)
    btn_stop = ft.ElevatedButton("توقف و ذخیره", on_click=stop_click, bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE, icon=ft.Icons.STOP, disabled=True)

    page.add(
        ft.Row([ft.Icon(ft.Icons.MUSIC_NOTE, size=40, color=C_MAIN), header], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        url_input,
        ft.Row([btn_start, btn_stop], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=10),
        ft.Row([ft.Text("شکار شده:", size=16), found_count], alignment=ft.MainAxisAlignment.CENTER),
        ft.Text("لاگ زنده:", weight=ft.FontWeight.BOLD),
        log_box
    )

ft.app(target=main)