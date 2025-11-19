# 4bbxy - V3.3 (Pastel Themes, Fast Sync, New Defaults)
# Requirements: pip install customtkinter requests

import os
import json
import threading
import time
from datetime import date, datetime
import requests

try:
    import customtkinter as ctk
except Exception:
    raise SystemExit("customtkinter not installed.")

# -------------------------
SETTINGS_FILE = "4bbxy_settings.json"
APP_NAME = "4bbxy"

# --- YENİ PASTEL VE GENİŞLETİLMİŞ TEMALAR ---
THEMES = {
    "Varsayılan (Mavi)":   {"bg": "#F7F8FB", "card": "#F0F4F8", "accent": "#D1E8FF", "text": "#2C3E50", "btn": "#5DADE2", "btn_hover": "#3498DB"},
    "Aşk (Pastel Pembe)":  {"bg": "#FFF0F5", "card": "#FFF5F7", "accent": "#FFD1DC", "text": "#6D4C41", "btn": "#FFB7C5", "btn_hover": "#FF9EAE"}, # Çok daha yumuşak pembe
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
    
    # Sync URLs
    "share_publish_url": "",
    "partner_fetch_url": "",
    
    # Partner Data
    "partner_today_seconds": 0,
    "partner_hearts": 0,
    "partner_total_hearts": 0,
    "partner_daily_target_minutes": 120,
    # <<< DEĞİŞTİ >>> Varsayılan not metni güncellendi
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
            if saved_date != date.today().isoformat():
                s["today_seconds"] = 0
                s["saved_date"] = date.today().isoformat()
                s["partner_today_seconds"] = 0
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
        
        # Tema Yükleme
        self.current_theme = THEMES.get(self.settings.get("theme_name"), THEMES["Varsayılan (Mavi)"])
        
        ctk.set_appearance_mode("Light")
        self.title(APP_NAME)
        self.geometry("800x550")
        self.minsize(750, 500)
        
        try: self.iconbitmap("icon.ico")
        except: pass

        self.configure(fg_color=self.current_theme["bg"])

        # --- TABS ---
        self.tabview = ctk.CTkTabview(self, width=760, height=500, fg_color=self.current_theme["card"],
                                      segmented_button_fg_color=self.current_theme["bg"],
                                      segmented_button_unselected_color=self.current_theme["bg"],
                                      text_color=self.current_theme["text"])
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_home = self.tabview.add("Ana Sayfa")
        self.tab_shop = self.tabview.add("Yarışma & Market")
        self.tab_settings = self.tabview.add("Ayarlar")

        self.tabview.configure(segmented_button_selected_color=self.current_theme["btn"])
        self.tabview.configure(segmented_button_selected_hover_color=self.current_theme["btn_hover"])

        self.setup_home_tab()
        self.setup_shop_tab()
        self.setup_settings_tab()

        self.timer = StudyTimer(initial_seconds=self.settings.get("today_seconds", 0), on_tick_callback=self._on_tick)
        self._update_time_display(self.settings.get("today_seconds", 0))
        self._update_progress_bars(self.settings.get("today_seconds", 0))

        self.auto_fetch_partner()
        self.auto_publish()
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------------------------------------------------
    # TAB 1: ANA SAYFA
    # ---------------------------------------------------------
    def setup_home_tab(self):
        top_frame = ctk.CTkFrame(self.tab_home, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=10)

        self.my_note_var = ctk.StringVar(value=self.settings.get("my_note"))
        self.my_note_entry = ctk.CTkEntry(top_frame, textvariable=self.my_note_var, font=ctk.CTkFont(size=14), 
                                          fg_color="white", text_color="black", border_color=self.current_theme["accent"])
        self.my_note_entry.pack(fill="x", pady=(0,5))
        self.my_note_entry.bind("<Return>", self.save_note_and_publish)
        # İlk tıklandığında varsayılan yazıyı silmek için (opsiyonel ama hoş)
        self.my_note_entry.bind("<FocusIn>", self.clear_placeholder)

        self.partner_note_label = ctk.CTkLabel(top_frame, text="Partner: " + self.settings.get("partner_note"),
                                      font=ctk.CTkFont(size=12, slant="italic"), text_color=self.current_theme["text"], anchor="w")
        self.partner_note_label.pack(fill="x")

        mid_frame = ctk.CTkFrame(self.tab_home, fg_color="white", corner_radius=15)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.time_var = ctk.StringVar(value="00:00:00")
        self.lbl_timer = ctk.CTkLabel(mid_frame, textvariable=self.time_var, font=ctk.CTkFont(size=60, weight="bold"), text_color=self.current_theme["text"])
        self.lbl_timer.pack(pady=(30, 10))

        btn_frame = ctk.CTkFrame(mid_frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        self.start_btn = ctk.CTkButton(btn_frame, text="BAŞLA", width=140, height=40, 
                                       fg_color=self.current_theme["btn"], hover_color=self.current_theme["btn_hover"],
                                       command=self.start_timer)
        self.start_btn.grid(row=0, column=0, padx=10)
        
        self.stop_btn = ctk.CTkButton(btn_frame, text="DURAKLAT", width=140, height=40, state="disabled",
                                      fg_color="#E74C3C", hover_color="#C0392B",
                                      command=self.stop_timer)
        self.stop_btn.grid(row=0, column=1, padx=10)

        progress_container = ctk.CTkFrame(mid_frame, fg_color="transparent")
        progress_container.pack(fill="x", padx=20, pady=30)

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
            ("👋 Selam Gönder", 2, "partnerine selam gönderdi!"),
            ("💋 Öpücük Gönder", 5, "sana kocaman bir öpücük gönderdi! Muah!"),
            ("☕ Kahve Ismarla", 8, "sana sanal bir kahve gönderdi. Mola ver!"),
            ("🎉 Konfeti Patlat", 12, "başarını kutluyor! Harikasın!"),
            ("⚠️ Çalış Uyarısı", 15, "DERSİNE DÖN! Gözüm üzerinde!")
        ]
        
        for name, cost, effect_msg in items:
            item_btn = ctk.CTkButton(market_frame, text=f"{name} ({cost} Kalp)", 
                                     fg_color="white", text_color="black", border_color=self.current_theme["btn"], border_width=2,
                                     hover_color="#EEE",
                                     command=lambda c=cost, m=effect_msg: self.buy_item(c, m))
            item_btn.pack(fill="x", pady=4, padx=20)
            
        ctk.CTkLabel(market_frame, text="* Her 30 dk çalışma = 1 Kalp", font=ctk.CTkFont(size=10), text_color="gray").pack(side="bottom", pady=10)

    # ---------------------------------------------------------
    # TAB 3: AYARLAR
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

        ctk.CTkLabel(set_frame, text="Tema Seçimi", font=ctk.CTkFont(weight="bold"), text_color=self.current_theme["text"]).pack(pady=(30,5))
        self.theme_var = ctk.StringVar(value=self.settings.get("theme_name", "Varsayılan (Mavi)"))
        
        theme_menu = ctk.CTkOptionMenu(set_frame, variable=self.theme_var, values=list(THEMES.keys()),
                                       fg_color=self.current_theme["btn"], button_color=self.current_theme["btn_hover"],
                                       command=self.change_theme)
        theme_menu.pack(pady=5)
        
        ctk.CTkLabel(set_frame, text="* Tema değişikliği için uygulamayı\nyeniden başlatman gerekebilir.", text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=5)

    # ---------------------------------------------------------
    # LOGIC & ACTIONS
    # ---------------------------------------------------------
    def clear_placeholder(self, event):
        if self.my_note_var.get() == "Notunu göndermek için buraya gir.":
            self.my_note_var.set("")

    def buy_item(self, cost, message):
        current_hearts = self.settings.get("hearts", 0)
        if current_hearts >= cost:
            self.settings["hearts"] = current_hearts - cost
            save_settings(self.settings)
            self.lbl_wallet.configure(text=f"💰 Harcanabilir Kalplerin: {self.settings['hearts']}")
            self.settings["outgoing_action"] = message
            self.settings["outgoing_action_id"] = str(time.time())
            self.publish_stats()
            import tkinter.messagebox as mb
            mb.showinfo("Başarılı", f"Hediye gönderildi! ({cost} kalp harcandı)")
        else:
            import tkinter.messagebox as mb
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
        self.publish_stats()

    def _on_tick(self, total_seconds):
        self.after(0, lambda: self._update_time_display(total_seconds))

    def _update_time_display(self, total_seconds):
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        self.time_var.set(f"{h:02d}:{m:02d}:{s:02d}")

    def _update_progress_bars(self, my_seconds):
        my_target = self.settings.get("daily_target_minutes", 120)
        my_ratio = min(1.0, my_seconds / (my_target * 60))
        self.progress.set(my_ratio)
        self.progress_text.configure(text=f"{int(my_seconds/60)} / {my_target} dk")

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
        # <<< DEĞİŞTİ >>> 10 saniyede 1 güncelleme
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
                        self.after(0, lambda m=incoming_msg: self.show_action_popup(m))

                    save_settings(self.settings)
                    self.after(0, lambda: self._update_progress_bars(self.timer.get_current_live_seconds()))
                    self.after(0, lambda: self.partner_note_label.configure(text="Partner: " + self.settings["partner_note"]))
                    self.after(0, lambda: self.lbl_partner_total.configure(text=f"PARTNER: {self.settings['partner_total_hearts']}"))
            except: pass
        threading.Thread(target=_fetch, daemon=True).start()

    def show_action_popup(self, message):
        import tkinter.messagebox as mb
        mb.showinfo("Partnerinden Mesaj Var! ❤️", f"Partnerin {message}")

    def auto_fetch_partner(self):
        try: self.fetch_partner_stats(is_auto=True)
        except: pass
        # <<< DEĞİŞTİ >>> 10 saniyede 1 güncelleme
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
