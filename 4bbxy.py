# 4bbxy - V5.2 (Compact Mini Mode Fix & To-Do Removed)
# Requirements: pip install customtkinter requests

import os
import json
import threading
import time
import random
from datetime import date, datetime, timedelta
import requests

# --- WINSOUND GÜVENLİ İMPORT ---
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("Kritik Hata: 'customtkinter' kütüphanesi yüklü değil. Lütfen 'pip install customtkinter' komutunu çalıştırın.")

# -------------------------
SETTINGS_FILE = "4bbxy_settings.json"
APP_NAME = "4bbxy"
YKS_DATE_STR = "2026-06-20 10:15:00" 

# --- TEMALAR ---
THEMES = {
    "Varsayılan (Mavi)":   {"bg": "#F7F8FB", "card": "#F0F4F8", "accent": "#D1E8FF", "text": "#2C3E50", "btn": "#5DADE2", "btn_hover": "#3498DB"},
    "Aşk (Pastel Pembe)":  {"bg": "#FFF0F5", "card": "#FFF5F7", "accent": "#FFD1DC", "text": "#6D4C41", "btn": "#FFB7C5", "btn_hover": "#FF9EAE"}, 
    "Lavanta (Mor)":       {"bg": "#F3E5F5", "card": "#F8F0FB", "accent": "#E1BEE7", "text": "#4A148C", "btn": "#BA68C8", "btn_hover": "#AB47BC"},
    "Nane (Yeşil)":        {"bg": "#E0F2F1", "card": "#E8F5E9", "accent": "#B9F6CA", "text": "#004D40", "btn": "#66BB6A", "btn_hover": "#43A047"},
    "Kahve (Toprak)":      {"bg": "#EFEBE9", "card": "#F5F5F5", "accent": "#D7CCC8", "text": "#3E2723", "btn": "#8D6E63", "btn_hover": "#6D4C41"},
    "Gece (Koyu)":         {"bg": "#212121", "card": "#303030", "accent": "#424242", "text": "#E0E0E0", "btn": "#424242", "btn_hover": "#616161"},
    "Okyanus (Turkuaz)":   {"bg": "#E0F7FA", "card": "#E0FFFF", "accent": "#80DEEA", "text": "#006064", "btn": "#4DD0E1", "btn_hover": "#26C6DA"},
}

DEFAULT_SETTINGS = {
    "daily_target_minutes": 120,
    "today_seconds": 0,
    "hearts": 0,            
    "total_hearts_ever": 0, 
    "last_heart_date": None,
    
    # Streak (Zincir) Sistemi
    "streak_count": 0,
    "last_streak_date": "", 
    
    # Ayarlar
    "always_on_top": False,

    # Sync URLs
    "share_publish_url": "",
    "partner_fetch_url": "",
    
    # Partner Data
    "partner_today_seconds": 0,
    "partner_hearts": 0,
    "partner_total_hearts": 0,
    "partner_daily_target_minutes": 120,
    "my_note": "Notunu göndermek için buraya gir.",
    "partner_note": "...",
    
    "theme_name": "Varsayılan (Mavi)",
    "incoming_action": "", 
    "last_action_id": ""
}

MIN_TARGET_MINUTES = 120
HEART_EARN_RATE_SECONDS = 1800 

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                if k not in s:
                    s[k] = v
            
            saved_date = s.get("saved_date")
            today_str = date.today().isoformat()
            
            if saved_date != today_str:
                s["today_seconds"] = 0
                s["saved_date"] = today_str
                s["partner_today_seconds"] = 0
                s["hearts_earned_today_count"] = 0
                
                last_s_date = s.get("last_streak_date", "")
                if last_s_date:
                    try:
                        last_dt = date.fromisoformat(last_s_date)
                        delta = (date.today() - last_dt).days
                        if delta > 1:
                            s["streak_count"] = 0
                    except: pass
                
                save_settings(s)
            return s
        except:
            return DEFAULT_SETTINGS.copy()
    else:
        s = DEFAULT_SETTINGS.copy()
        s["saved_date"] = date.today().isoformat()
        save_settings(s)
        return s

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Save error:", e)

# -------------------------
class StudyTimer:
    def __init__(self, initial_seconds=0, on_tick_callback=None):
        self._running = False
        self._start_time = None
        self._accum_seconds = initial_seconds
        self._thread = None
        self.on_tick = on_tick_callback

    def start(self):
        if self._running: return
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._running: return 0
        self._running = False
        elapsed = int(time.time() - self._start_time)
        self._accum_seconds += elapsed
        self._start_time = None
        return elapsed

    def get_current_live_seconds(self):
        if self._running and self._start_time is not None:
            return int(time.time() - self._start_time) + self._accum_seconds
        return self._accum_seconds

    def _run(self):
        while self._running:
            elapsed = int(time.time() - self._start_time) + self._accum_seconds
            if self.on_tick:
                try: self.on_tick(elapsed)
                except: pass
            time.sleep(1)

# -------------------------
class FourBBXYApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        
        self.current_theme = THEMES.get(self.settings.get("theme_name"), THEMES["Varsayılan (Mavi)"])
        
        ctk.set_appearance_mode("Light")
        self.title(APP_NAME)
        
        # Başlangıç Boyutları
        self.geometry("800x600")
        self.minsize(750, 500)
        
        try: self.iconbitmap("icon.ico")
        except: pass

        self.configure(fg_color=self.current_theme["bg"])

        if self.settings.get("always_on_top", False):
            self.attributes("-topmost", True)

        # --- UI ---
        self.tabview = ctk.CTkTabview(self, width=760, height=550, fg_color=self.current_theme["card"],
                                      segmented_button_fg_color=self.current_theme["bg"],
                                      segmented_button_unselected_color=self.current_theme["bg"],
                                      text_color=self.current_theme["text"])
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_home = self.tabview.add("Ana Sayfa")
        self.tab_shop = self.tabview.add("Yarışma & Market")
        self.tab_yks  = self.tabview.add("YKS")
        self.tab_settings = self.tabview.add("Ayarlar")

        self.tabview.configure(segmented_button_selected_color=self.current_theme["btn"])
        self.tabview.configure(segmented_button_selected_hover_color=self.current_theme["btn_hover"])

        # Mini Mode Frame (Başlangıçta gizli)
        self.mini_frame = ctk.CTkFrame(self, fg_color=self.current_theme["bg"])
        self.setup_mini_mode_ui()

        self.setup_home_tab()
        self.setup_shop_tab()
        self.setup_yks_tab()
        self.setup_settings_tab()

        self.timer = StudyTimer(initial_seconds=self.settings.get("today_seconds", 0), on_tick_callback=self._on_tick)
        self._update_time_display(self.settings.get("today_seconds", 0))
        self._update_progress_bars(self.settings.get("today_seconds", 0))
        self.update_streak_display()

        self.auto_fetch_partner()
        self.auto_publish()
        self.update_yks_countdown()
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------------------------------------------------
    # MINI MODE UI (COMPACT)
    # ---------------------------------------------------------
    def setup_mini_mode_ui(self):
        # İçerik ortalansın
        container = ctk.CTkFrame(self.mini_frame, fg_color="transparent")
        container.pack(expand=True)

        self.mini_time_var = ctk.StringVar(value="00:00:00")
        self.lbl_mini_timer = ctk.CTkLabel(container, textvariable=self.mini_time_var, 
                                           font=ctk.CTkFont(size=32, weight="bold"), text_color=self.current_theme["text"])
        self.lbl_mini_timer.pack(pady=(5, 5))
        
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=2)
        
        self.mini_stop_btn = ctk.CTkButton(btn_frame, text="⏸", width=30, height=25, fg_color="#E74C3C", command=self.stop_timer)
        self.mini_stop_btn.grid(row=0, column=0, padx=2)
        
        self.mini_start_btn = ctk.CTkButton(btn_frame, text="▶", width=30, height=25, fg_color=self.current_theme["btn"], command=self.start_timer)
        self.mini_start_btn.grid(row=0, column=1, padx=2)
        
        ctk.CTkButton(container, text="Genişlet ⤢", width=80, height=20, fg_color="gray", font=ctk.CTkFont(size=10),
                      command=self.toggle_mini_mode).pack(pady=5)

    def toggle_mini_mode(self):
        if self.tabview.winfo_ismapped():
            # --- MINI MODA GEÇİŞ ---
            self.tabview.pack_forget()
            
            # Pencereyi küçültmek için önce minsize kısıtlamasını kırıyoruz
            self.minsize(200, 120) 
            self.geometry("220x130") # Çok daha kompakt bir boyut
            
            self.mini_frame.pack(fill="both", expand=True)
            self.attributes("-topmost", True) 
        else:
            # --- NORMAL MODA GEÇİŞ ---
            self.mini_frame.pack_forget()
            
            # Normal boyut kısıtlamalarını geri yükle
            self.minsize(750, 500)
            self.geometry("800x600")
            
            self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
            self.attributes("-topmost", self.settings.get("always_on_top", False))

    # ---------------------------------------------------------
    # TAB 1: ANA SAYFA
    # ---------------------------------------------------------
    def setup_home_tab(self):
        top_frame = ctk.CTkFrame(self.tab_home, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=5)
        
        left_top = ctk.CTkFrame(top_frame, fg_color="transparent")
        left_top.pack(side="left", fill="x", expand=True)
        
        self.my_note_var = ctk.StringVar(value=self.settings.get("my_note"))
        self.my_note_entry = ctk.CTkEntry(left_top, textvariable=self.my_note_var, font=ctk.CTkFont(size=14), 
                                          fg_color="white", text_color="black", border_color=self.current_theme["accent"])
        self.my_note_entry.pack(fill="x", pady=(0,2))
        self.my_note_entry.bind("<Return>", self.save_note_and_publish)
        self.my_note_entry.bind("<FocusIn>", self.clear_placeholder)
        
        self.partner_note_label = ctk.CTkLabel(left_top, text="Partner: " + str(self.settings.get("partner_note")),
                                     font=ctk.CTkFont(size=12, slant="italic"), text_color=self.current_theme["text"], anchor="w")
        self.partner_note_label.pack(fill="x")

        self.streak_label = ctk.CTkLabel(top_frame, text="🔥 0 Gün", font=ctk.CTkFont(size=16, weight="bold"), text_color="#E67E22")
        self.streak_label.pack(side="right", padx=10)

        mid_frame = ctk.CTkFrame(self.tab_home, fg_color="white", corner_radius=15)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=20) # expand=True ile ortaladık

        self.time_var = ctk.StringVar(value="00:00:00")
        self.lbl_timer = ctk.CTkLabel(mid_frame, textvariable=self.time_var, font=ctk.CTkFont(size=70, weight="bold"), text_color=self.current_theme["text"])
        self.lbl_timer.pack(pady=(40, 20))

        btn_frame = ctk.CTkFrame(mid_frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        self.start_btn = ctk.CTkButton(btn_frame, text="BAŞLA", width=140, height=45, 
                                     fg_color=self.current_theme["btn"], hover_color=self.current_theme["btn_hover"],
                                     command=self.start_timer)
        self.start_btn.grid(row=0, column=0, padx=10)
        
        self.stop_btn = ctk.CTkButton(btn_frame, text="DURAKLAT", width=140, height=45, state="disabled",
                                     fg_color="#E74C3C", hover_color="#C0392B",
                                     command=self.stop_timer)
        self.stop_btn.grid(row=0, column=1, padx=10)

        progress_container = ctk.CTkFrame(mid_frame, fg_color="transparent")
        progress_container.pack(fill="x", padx=20, pady=40)

        left_prog = ctk.CTkFrame(progress_container, fg_color="transparent")
        left_prog.pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkLabel(left_prog, text="Senin İlerlemen", text_color=self.current_theme["text"]).pack(anchor="w")
        self.progress = ctk.CTkProgressBar(left_prog, height=15, progress_color=self.current_theme["btn"])
        self.progress.set(0)
        self.progress.pack(fill="x", pady=5)
        self.progress_text = ctk.CTkLabel(left_prog, text="0 / 120 dk", text_color="gray")
        self.progress_text.pack(anchor="w")

        right_prog = ctk.CTkFrame(progress_container, fg_color="transparent")
        right_prog.pack(side="right", fill="x", expand=True, padx=10)
        ctk.CTkLabel(right_prog, text="Partnerin İlerlemesi", text_color=self.current_theme["text"]).pack(anchor="w")
        self.partner_progress = ctk.CTkProgressBar(right_prog, height=15, progress_color="#E67E22")
        self.partner_progress.set(0)
        self.partner_progress.pack(fill="x", pady=5)
        self.partner_progress_text = ctk.CTkLabel(right_prog, text="0 / 120 dk", text_color="gray")
        self.partner_progress_text.pack(anchor="w")

    # ---------------------------------------------------------
    # TAB 2: YARIŞMA & MARKET
    # ---------------------------------------------------------
    def setup_shop_tab(self):
        score_frame = ctk.CTkFrame(self.tab_shop, fg_color="white", corner_radius=10)
        score_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(score_frame, text="🏆 Liderlik Tablosu (Toplam Kalp) 🏆", font=ctk.CTkFont(weight="bold", size=16), text_color=self.current_theme["text"]).pack(pady=10)
        
        score_grid = ctk.CTkFrame(score_frame, fg_color="transparent")
        score_grid.pack(fill="x", padx=20, pady=(0,20))

        self.lbl_my_total = ctk.CTkLabel(score_grid, text=f"SEN: {self.settings.get('total_hearts_ever', 0)}", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.current_theme["btn"])
        self.lbl_my_total.pack(side="left", expand=True)
        
        ctk.CTkLabel(score_grid, text="VS", font=ctk.CTkFont(size=14, slant="italic"), text_color="gray").pack(side="left", padx=10)
        
        self.lbl_partner_total = ctk.CTkLabel(score_grid, text=f"PARTNER: {self.settings.get('partner_total_hearts', 0)}", font=ctk.CTkFont(size=20, weight="bold"), text_color="#E67E22")
        self.lbl_partner_total.pack(side="right", expand=True)

        market_frame = ctk.CTkFrame(self.tab_shop, fg_color="transparent")
        market_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        wallet_frame = ctk.CTkFrame(market_frame, fg_color=self.current_theme["accent"])
        wallet_frame.pack(fill="x", pady=(0,10))
        self.lbl_wallet = ctk.CTkLabel(wallet_frame, text=f"💰 Harcanabilir Kalplerin: {self.settings.get('hearts', 0)}", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.current_theme["text"])
        self.lbl_wallet.pack(pady=10)
        
        ctk.CTkLabel(market_frame, text="✨ Partnerine Etkileşim Gönder ✨", font=ctk.CTkFont(size=14), text_color=self.current_theme["text"]).pack(pady=5)
        
        items = [
            ("👋 Selam Gönder", 2, "sana selam gönderdi!"),
            ("💋 Öpücük Gönder", 5, "sana kocaman bir öpücük gönderdi! Muah!"),
            ("☕ Kahve Ismarla", 8, "sana sanal bir kahve gönderdi. Mola ver!"),
            ("🎉 Konfeti Patlat", 12, "başarını kutluyor! Harikasın!"),
            ("⚠️ Çalış Uyarısı", 15, "seni uyarıyor: DERSİNE DÖN! Gözüm üzerinde!"),
            ("👻 JUMPSCARE (50)", 50, "jumpscare")
        ]
        
        for name, cost, effect_msg in items:
            btn_color = "#E74C3C" if cost == 50 else self.current_theme["btn"]
            btn_hover = "#C0392B" if cost == 50 else self.current_theme["btn_hover"]

            item_btn = ctk.CTkButton(market_frame, text=f"{name} ({cost} Kalp)", 
                                     fg_color=btn_color,
                                     text_color="white",
                                     hover_color=btn_hover,
                                     command=lambda c=cost, m=effect_msg: self.buy_item(c, m))
            item_btn.pack(fill="x", pady=4, padx=20)
            
        ctk.CTkLabel(market_frame, text="* Her 30 dk çalışma = 1 Kalp", font=ctk.CTkFont(size=10), text_color="gray").pack(side="bottom", pady=10)

    # ---------------------------------------------------------
    # TAB 3: YKS SAYACI
    # ---------------------------------------------------------
    def setup_yks_tab(self):
        yks_frame = ctk.CTkFrame(self.tab_yks, fg_color="white", corner_radius=20)
        yks_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(yks_frame, text="🎓 YKS'YE KALAN SÜRE 🎓", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.current_theme["text"]).pack(pady=(40, 20))
        
        count_container = ctk.CTkFrame(yks_frame, fg_color="transparent")
        count_container.pack(pady=20)

        self.lbl_days = ctk.CTkLabel(count_container, text="000", font=ctk.CTkFont(size=50, weight="bold"), text_color="#E74C3C")
        self.lbl_days.grid(row=0, column=0, padx=15)
        ctk.CTkLabel(count_container, text="GÜN", font=ctk.CTkFont(size=14), text_color="gray").grid(row=1, column=0)

        self.lbl_hours = ctk.CTkLabel(count_container, text="00", font=ctk.CTkFont(size=50, weight="bold"), text_color=self.current_theme["text"])
        self.lbl_hours.grid(row=0, column=1, padx=15)
        ctk.CTkLabel(count_container, text="SAAT", font=ctk.CTkFont(size=14), text_color="gray").grid(row=1, column=1)
        
        self.lbl_minutes = ctk.CTkLabel(count_container, text="00", font=ctk.CTkFont(size=50, weight="bold"), text_color=self.current_theme["text"])
        self.lbl_minutes.grid(row=0, column=2, padx=15)
        ctk.CTkLabel(count_container, text="DAKİKA", font=ctk.CTkFont(size=14), text_color="gray").grid(row=1, column=2)
        
        self.lbl_seconds = ctk.CTkLabel(count_container, text="00", font=ctk.CTkFont(size=50, weight="bold"), text_color=self.current_theme["btn"])
        self.lbl_seconds.grid(row=0, column=3, padx=15)
        ctk.CTkLabel(count_container, text="SANİYE", font=ctk.CTkFont(size=14), text_color="gray").grid(row=1, column=3)
        
        quotes = [
            "Hayallerin uyumaktan daha tatlıysa,\nkalk ve çalışmaya başla.",
            "Başarı tesadüf değildir.",
            "O üniversite kapısından içeri gireceksin!",
            "Bugün yaptıkların yarınını belirleyecek.",
            "Pes etmek yok, yola devam!"
        ]
        quote = random.choice(quotes)
        ctk.CTkLabel(yks_frame, text=f'"{quote}"', font=ctk.CTkFont(size=16, slant="italic"), text_color="gray").pack(side="bottom", pady=40)

    def update_yks_countdown(self):
        try:
            target = datetime.strptime(YKS_DATE_STR, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            remaining = target - now
            
            if remaining.total_seconds() > 0:
                days = remaining.days
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                self.lbl_days.configure(text=f"{days:03d}")
                self.lbl_hours.configure(text=f"{hours:02d}")
                self.lbl_minutes.configure(text=f"{minutes:02d}")
                self.lbl_seconds.configure(text=f"{seconds:02d}")
            else:
                self.lbl_days.configure(text="000")
                self.lbl_hours.configure(text="00")
                self.lbl_minutes.configure(text="00")
                self.lbl_seconds.configure(text="00")
        except:
            pass
        self.after(1000, self.update_yks_countdown)

    # ---------------------------------------------------------
    # TAB 4: AYARLAR (Mini Mod Butonu Eklendi)
    # ---------------------------------------------------------
    def setup_settings_tab(self):
        set_frame = ctk.CTkFrame(self.tab_settings, fg_color="white")
        set_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(set_frame, text="Günlük Hedef (Dakika)", font=ctk.CTkFont(weight="bold"), text_color=self.current_theme["text"]).pack(pady=(20,5))
        
        target_frame = ctk.CTkFrame(set_frame, fg_color="transparent")
        target_frame.pack()
        self.target_var = ctk.IntVar(value=self.settings.get("daily_target_minutes", 120))
        ctk.CTkEntry(target_frame, textvariable=self.target_var, width=80, justify="center").pack(side="left", padx=5)
        ctk.CTkButton(target_frame, text="Kaydet", width=80, fg_color=self.current_theme["btn"], command=self.save_target).pack(side="left", padx=5)

        # --- PENCERE AYARLARI ---
        ctk.CTkLabel(set_frame, text="Pencere Ayarları", font=ctk.CTkFont(weight="bold"), text_color=self.current_theme["text"]).pack(pady=(20,5))
        
        # Always on Top
        self.aot_switch = ctk.CTkSwitch(set_frame, text="Her Zaman Üstte Kal", command=self.toggle_always_on_top,
                                        progress_color=self.current_theme["btn"])
        if self.settings.get("always_on_top", False):
            self.aot_switch.select()
        self.aot_switch.pack(pady=5)

        # Mini Mod Butonu (BURAYA TAŞINDI)
        ctk.CTkButton(set_frame, text="MİNİ MODU AÇ", width=150, height=35, 
                      fg_color="gray", hover_color="#555", 
                      command=self.toggle_mini_mode).pack(pady=10)

        # Tema
        ctk.CTkLabel(set_frame, text="Tema Seçimi", font=ctk.CTkFont(weight="bold"), text_color=self.current_theme["text"]).pack(pady=(20,5))
        self.theme_var = ctk.StringVar(value=self.settings.get("theme_name", "Varsayılan (Mavi)"))
        
        theme_menu = ctk.CTkOptionMenu(set_frame, variable=self.theme_var, values=list(THEMES.keys()),
                                     fg_color=self.current_theme["btn"], button_color=self.current_theme["btn_hover"],
                                     command=self.change_theme)
        theme_menu.pack(pady=5)
        
        ctk.CTkLabel(set_frame, text="* Tema değişikliği için uygulamayı\nyeniden başlatman gerekebilir.", text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=5)

    def toggle_always_on_top(self):
        val = bool(self.aot_switch.get())
        self.settings["always_on_top"] = val
        self.attributes("-topmost", val)
        save_settings(self.settings)

    # ---------------------------------------------------------
    # LOGIC & ACTIONS
    # ---------------------------------------------------------
    def clear_placeholder(self, event):
        if self.my_note_var.get() == "Notunu göndermek için buraya gir.":
            self.my_note_var.set("")

    def buy_item(self, cost, message):
        import tkinter.messagebox as mb
        current_hearts = self.settings.get("hearts", 0)
        if current_hearts >= cost:
            self.settings["hearts"] = current_hearts - cost
            save_settings(self.settings)
            self.lbl_wallet.configure(text=f"💰 Harcanabilir Kalplerin: {self.settings['hearts']}")
            self.settings["outgoing_action"] = message
            self.settings["outgoing_action_id"] = str(time.time())
            self.publish_stats()
            mb.showinfo("Başarılı", f"Hediye gönderildi! ({cost} kalp harcandı)")
        else:
            mb.showerror("Yetersiz Bakiye", "Yeterli kalbin yok! Biraz daha ders çalışmalısın.")

    def change_theme(self, new_theme_name):
        self.settings["theme_name"] = new_theme_name
        save_settings(self.settings)
        import tkinter.messagebox as mb
        mb.showinfo("Tema Değişti", "Yeni temanın tam olarak uygulanması için lütfen uygulamayı kapatıp tekrar açın.")

    def save_target(self):
        try:
            val = int(self.target_var.get())
            if val < MIN_TARGET_MINUTES:
                self.target_var.set(MIN_TARGET_MINUTES)
                val = MIN_TARGET_MINUTES
            self.settings["daily_target_minutes"] = val
            save_settings(self.settings)
            self._update_progress_bars(self.timer.get_current_live_seconds())
            self.publish_stats()
        except:
            pass

    def save_note_and_publish(self, event=None):
        self.settings["my_note"] = self.my_note_var.get()
        save_settings(self.settings)
        self.publish_stats()
        self.my_note_entry.master.focus()

    def start_timer(self):
        self.timer.start()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.mini_start_btn.configure(state="disabled")
        self.mini_stop_btn.configure(state="normal")

    def stop_timer(self):
        self.timer.stop()
        final_seconds = self.timer.get_current_live_seconds()
        self.settings["today_seconds"] = final_seconds
        self.settings["saved_date"] = date.today().isoformat()
        save_settings(self.settings)
        self._update_time_display(final_seconds)
        self._update_progress_bars(final_seconds)
        
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.mini_start_btn.configure(state="normal")
        self.mini_stop_btn.configure(state="disabled")
        
        self.publish_stats()

    def _on_tick(self, total_seconds):
        self.after(0, lambda: self._update_time_display(total_seconds))

    def _update_time_display(self, total_seconds):
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        self.time_var.set(time_str)
        self.mini_time_var.set(time_str)

    def _update_progress_bars(self, my_seconds):
        my_target = self.settings.get("daily_target_minutes", 120)
        my_ratio = min(1.0, my_seconds / (my_target * 60))
        self.progress.set(my_ratio)
        self.progress_text.configure(text=f"{int(my_seconds/60)} / {my_target} dk")

        if my_seconds >= (my_target * 60):
            today_str = date.today().isoformat()
            last_streak = self.settings.get("last_streak_date", "")
            if last_streak != today_str:
                self.settings["streak_count"] = self.settings.get("streak_count", 0) + 1
                self.settings["last_streak_date"] = today_str
                save_settings(self.settings)
                self.update_streak_display()
                if WINSOUND_AVAILABLE:
                    try: winsound.Beep(1000, 200)
                    except: pass

        p_seconds = self.settings.get("partner_today_seconds", 0)
        p_target = self.settings.get("partner_daily_target_minutes", 120)
        p_ratio = min(1.0, p_seconds / (p_target * 60))
        self.partner_progress.set(p_ratio)
        self.partner_progress_text.configure(text=f"{int(p_seconds/60)} / {p_target} dk")

        hearts_earned_today = int(my_seconds / HEART_EARN_RATE_SECONDS)
        last_saved_hearts_today = self.settings.get("hearts_earned_today_count", 0)
        
        if self.settings.get("saved_date") != date.today().isoformat():
            last_saved_hearts_today = 0

        if hearts_earned_today > last_saved_hearts_today:
            diff = hearts_earned_today - last_saved_hearts_today
            self.settings["hearts"] = self.settings.get("hearts", 0) + diff
            self.settings["total_hearts_ever"] = self.settings.get("total_hearts_ever", 0) + diff
            self.settings["hearts_earned_today_count"] = hearts_earned_today
            save_settings(self.settings)
            
            self.lbl_wallet.configure(text=f"💰 Harcanabilir Kalplerin: {self.settings['hearts']}")
            self.lbl_my_total.configure(text=f"SEN: {self.settings['total_hearts_ever']}")
            
            import tkinter.messagebox as mb
            mb.showinfo("Tebrikler!", f"{diff} Kalp kazandın! Çalışmaya devam!")
            self.publish_stats()
    
    def update_streak_display(self):
        cnt = self.settings.get("streak_count", 0)
        self.streak_label.configure(text=f"🔥 {cnt} Gün")

    def publish_stats(self):
        url = self.settings.get("share_publish_url")
        if not url: return
        current_seconds = self.timer.get_current_live_seconds()
        payload = {
            "today_seconds": current_seconds, 
            "hearts": self.settings.get("hearts", 0),
            "total_hearts": self.settings.get("total_hearts_ever", 0),
            "last_update": date.today().isoformat(),
            "daily_target": self.settings.get("daily_target_minutes", 120),
            "note": self.settings.get("my_note", ""),
            "action_msg": self.settings.get("outgoing_action", ""),
            "action_id": self.settings.get("outgoing_action_id", "")
        }
        def _upload():
            try: requests.post(url, json=payload, timeout=10)
            except: pass
        threading.Thread(target=_upload, daemon=True).start()

    def auto_publish(self):
        try:
            if self.timer._running: self.publish_stats()
        except: pass
        self.after(10000, self.auto_publish)

    def fetch_partner_stats(self, is_auto=False):
        url = self.settings.get("partner_fetch_url")
        if not url: return

        def _fetch():
            try:
                cache_bust = f"?v={int(time.time())}"
                resp = requests.get(url + cache_bust, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    self.after(0, lambda: self._process_partner_data(data))
            except: pass
        
        threading.Thread(target=_fetch, daemon=True).start()

    def _process_partner_data(self, data):
        today = date.today().isoformat()
        if data.get("last_update") == today:
            self.settings["partner_today_seconds"] = data.get("today_seconds", 0)
        else:
            self.settings["partner_today_seconds"] = 0
        
        self.settings["partner_hearts"] = data.get("hearts", 0) 
        self.settings["partner_total_hearts"] = data.get("total_hearts", 0) 
        self.settings["partner_daily_target_minutes"] = data.get("daily_target", 120)
        self.settings["partner_note"] = data.get("note", "...")
        
        incoming_id = data.get("action_id", "")
        incoming_msg = data.get("action_msg", "")
        
        last_seen_id = self.settings.get("last_action_id", "")
        if incoming_id and incoming_id != last_seen_id:
            self.settings["last_action_id"] = incoming_id
            save_settings(self.settings)
            
            if incoming_msg == "jumpscare":
                self.trigger_jumpscare()
            else:
                self.show_action_popup(incoming_msg)

        save_settings(self.settings)
        self._update_progress_bars(self.timer.get_current_live_seconds())
        self.partner_note_label.configure(text="Partner: " + str(self.settings["partner_note"]))
        self.lbl_partner_total.configure(text=f"PARTNER: {self.settings['partner_total_hearts']}")

    def show_action_popup(self, message):
        import tkinter.messagebox as mb
        mb.showinfo("Partnerinden Mesaj Var! ❤️", f"Partnerin {message}")

    def trigger_jumpscare(self):
        if not WINSOUND_AVAILABLE: return
        sound_file = "Jumpscare Sound.wav"
        if os.path.exists(sound_file):
            winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            def play_chaos_sound():
                for _ in range(20):
                    freq = random.randint(500, 3000)
                    dur = random.randint(50, 100)
                    try: winsound.Beep(freq, dur)
                    except: pass
                    time.sleep(0.02)
            threading.Thread(target=play_chaos_sound, daemon=True).start()

    def auto_fetch_partner(self):
        try: self.fetch_partner_stats(is_auto=True)
        except: pass
        self.after(10000, self.auto_fetch_partner)

    def _on_close(self):
        if self.timer._running: self.timer.stop()
        self.settings["today_seconds"] = self.timer.get_current_live_seconds()
        self.publish_stats()
        save_settings(self.settings)
        time.sleep(0.5)
        self.destroy()

if __name__ == "__main__":
    app = FourBBXYApp()
    app.mainloop()
