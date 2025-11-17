# 4bbxy - updated stable version (Müzik özelliği kaldırıldı)
# Requirements:
#   pip install customtkinter requests

import os
import json
import threading
import time
from datetime import date, datetime
import requests

# UI lib
try:
    import customtkinter as ctk
except Exception:
    raise SystemExit("customtkinter not installed. Install with: pip install customtkinter")

# <<< DEĞİŞTİ >>> Pygame ve ses ile ilgili her şey kaldırıldı.

# -------------------------
SETTINGS_FILE = "4bbxy_settings.json"
APP_NAME = "4bbxy"

PALETTE = {
    "bg": "#F7F8FB",
    "card": "#F9EAF1",
    "accent": "#B7D3DF",
    "muted": "#E4D9FF",
    "text": "#2E2E2E",
    "success": "#9FD5B8"
}

# -------------------------
DEFAULT_SETTINGS = {
    "daily_target_minutes": 120,
    "today_seconds": 0,
    "hearts": 0,
    # <<< DEĞİŞTİ >>> "sound_on": False, kaldırıldı
    "last_heart_date": None,
    "share_publish_url": "",   # Kendi verilerini yayınlama URL'si (npoint.io)
    "partner_fetch_url": "",   # Partner verilerini çekme URL'si (npoint.io)
    "partner_today_seconds": 0,
    "partner_hearts": 0,
    "partner_daily_target_minutes": 120,
    "my_note": "Notunuzu buraya yazın ve Enter'a basın...",
    "partner_note": "Partnerin notu..." 
}

MIN_TARGET_MINUTES = 120   # enforce minimum

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
            # fill defaults
            for k, v in DEFAULT_SETTINGS.items():
                if k not in s:
                    s[k] = v
            # reset today's seconds if date changed
            saved_date = s.get("saved_date")
            if saved_date != date.today().isoformat():
                s["today_seconds"] = 0
                s["saved_date"] = date.today().isoformat()
                s["target_reached_today"] = False
                s["partner_today_seconds"] = 0
                save_settings(s)
            return s
        except Exception:
            return DEFAULT_SETTINGS.copy()
    else:
        s = DEFAULT_SETTINGS.copy()
        s["saved_date"] = date.today().isoformat()
        s["target_reached_today"] = False
        save_settings(s)
        return s

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to save settings:", e)

# -------------------------
# <<< DEĞİŞTİ >>> AmbientPlayer sınıfı kaldırıldı.
# -------------------------

class StudyTimer:
    def __init__(self, initial_seconds=0, on_tick_callback=None):
        self._running = False
        self._start_time = None
        self._accum_seconds = initial_seconds
        self._thread = None
        self.on_tick = on_tick_callback

    def start(self):
        if self._running:
            return
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._running:
            return 0
        self._running = False
        elapsed = int(time.time() - self._start_time)
        self._accum_seconds += elapsed
        self._start_time = None
        return elapsed

    def get_current_live_seconds(self):
        """Zamanlayıcı çalışıyorsa o anki saniyeyi, çalışmıyorsa birikmiş saniyeyi döndürür."""
        if self._running and self._start_time is not None:
            return int(time.time() - self._start_time) + self._accum_seconds
        return self._accum_seconds

    def _run(self):
        while self._running:
            elapsed = int(time.time() - self._start_time) + self._accum_seconds
            if self.on_tick:
                try:
                    self.on_tick(elapsed)
                except Exception:
                    pass
            time.sleep(1)

    def reset_accum(self):
        self._accum_seconds = 0
        self._start_time = None
        self._running = False

# -------------------------
class FourBBXYApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.settings = load_settings()

        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")   # safe default

        self.title(APP_NAME)
        self.geometry("780x480")
        self.minsize(700, 440)
        self.configure(fg_color=PALETTE["bg"])

        # --- top frame
        top_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=PALETTE["card"])
        top_frame.pack(padx=20, pady=(20,10), fill="x")

        title_row = ctk.CTkFrame(top_frame, fg_color=PALETTE["card"])
        title_row.pack(fill="x", padx=12, pady=(12,6))
        self.lbl_app = ctk.CTkLabel(title_row, text=APP_NAME, font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_app.pack(side="left")

        hearts_frame = ctk.CTkFrame(title_row, fg_color="transparent")
        hearts_frame.pack(side="right")
        ctk.CTkLabel(hearts_frame, text="Sen:", font=ctk.CTkFont(size=14)).pack(side="left")
        self.lbl_hearts = ctk.CTkLabel(hearts_frame, text="♥ " + str(self.settings.get("hearts",0)),
                                       font=ctk.CTkFont(size=16, weight="bold"), text_color="#E74C3C")
        self.lbl_hearts.pack(side="left")
        ctk.CTkLabel(hearts_frame, text=" | Partner:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(10,0))
        self.lbl_partner_hearts = ctk.CTkLabel(hearts_frame, text="♥ " + str(self.settings.get("partner_hearts",0)),
                                       font=ctk.CTkFont(size=16, weight="bold"), text_color="#E67E22")
        self.lbl_partner_hearts.pack(side="left")

        self.my_note_var = ctk.StringVar(value=self.settings.get("my_note"))
        self.my_note_entry = ctk.CTkEntry(top_frame, textvariable=self.my_note_var, font=ctk.CTkFont(size=14))
        self.my_note_entry.pack(fill="x", padx=12, pady=(5,5))
        self.my_note_entry.bind("<Return>", self.save_note_and_publish)

        self.partner_note_label = ctk.CTkLabel(top_frame, text="Partner : " + self.settings.get("partner_note"),
                                      wraplength=680, justify="left",
                                      font=ctk.CTkFont(size=12, slant="italic"),
                                      text_color="#555", anchor="w")
        self.partner_note_label.pack(fill="x", padx=12, pady=(0,12))

        # --- middle
        mid_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="white")
        mid_frame.pack(padx=20, pady=6, fill="both", expand=True)

        left = ctk.CTkFrame(mid_frame, fg_color="white")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        self.time_var = ctk.StringVar(value="00:00:00")
        time_display = ctk.CTkLabel(left, textvariable=self.time_var, font=ctk.CTkFont(size=36, weight="bold"))
        time_display.pack(pady=(10,8))

        target_row = ctk.CTkFrame(left, fg_color="white")
        target_row.pack(pady=(6,10), fill="x", padx=8)
        ctk.CTkLabel(target_row, text="Günlük hedef (dakika):").pack(side="left")
        self.target_var = ctk.IntVar(value=self.settings.get("daily_target_minutes", DEFAULT_SETTINGS["daily_target_minutes"]))
        self.target_entry = ctk.CTkEntry(target_row, width=80, textvariable=self.target_var)
        self.target_entry.pack(side="left", padx=8)
        save_target_btn = ctk.CTkButton(target_row, text="Kaydet", width=80, command=self.save_target)
        save_target_btn.pack(side="left")

        self.target_error_label = ctk.CTkLabel(left, text=f"Günlük hedef minimum {MIN_TARGET_MINUTES} dakikadır.",
                                                text_color="red", font=ctk.CTkFont(size=12))

        ctrl_frame = ctk.CTkFrame(left, fg_color="white")
        ctrl_frame.pack(pady=8)
        self.start_btn = ctk.CTkButton(ctrl_frame, text="Start", width=120, command=self.start_timer)
        self.start_btn.grid(row=0, column=0, padx=6, pady=6)
        self.stop_btn = ctk.CTkButton(ctrl_frame, text="Stop", width=120, command=self.stop_timer, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=6, pady=6)

        progress_label = ctk.CTkLabel(left, text="Günlük ilerleme (Sen)")
        progress_label.pack(pady=(8,4))
        self.progress = ctk.CTkProgressBar(left, width=420)
        self.progress.set(0.0)
        self.progress.pack(pady=(0,12))
        self.progress_text = ctk.CTkLabel(left, text=self._progress_text())
        self.progress_text.pack()

        right = ctk.CTkFrame(mid_frame, fg_color="white")
        right.pack(side="right", fill="both", expand=True, padx=12, pady=12)

        reward_card = ctk.CTkFrame(right, fg_color=PALETTE["muted"], corner_radius=10)
        reward_card.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(reward_card, text="Kalp Ödülleri (Sen)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(8,0))
        self.reward_text = ctk.CTkLabel(reward_card, text=self._reward_text(), wraplength=260)
        self.reward_text.pack(pady=(6,12))

        partner_card = ctk.CTkFrame(right, fg_color=PALETTE["accent"], corner_radius=10)
        partner_card.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(partner_card, text="Partnerin İlerlemesi", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(8,0))

        self.partner_progress = ctk.CTkProgressBar(partner_card, width=240, progress_color="#E67E22")
        self.partner_progress.set(0.0)
        self.partner_progress.pack(pady=(8,4))
        self.partner_progress_text = ctk.CTkLabel(partner_card, text=self._partner_progress_text(), wraplength=260)
        self.partner_progress_text.pack(pady=(0,12))

        # <<< DEĞİŞTİ >>> sound_frame ve içindekiler kaldırıldı.
        # <<< DEĞİŞTİ >>> Senkronize Et butonu kaldırıldı.
        
        # Sadece boşluk olması için bir çerçeve bırakabiliriz (veya tamamen kaldırabiliriz)
        # Şimdilik tamamen kaldırıyorum, sağ taraf biraz daha sıkışık olacak.
        # refresh_row = ctk.CTkFrame(right, fg_color="white")
        # refresh_row.pack(fill="x", padx=6, pady=8)


        footer = ctk.CTkFrame(self, fg_color=PALETTE["bg"])
        footer.pack(fill="x", padx=20, pady=(6,20))
        ctk.CTkLabel(footer, text="4bbxy — made with love by soran", font=ctk.CTkFont(size=11)).pack(side="left")

        # timer with persisted initial seconds
        self.timer = StudyTimer(initial_seconds=self.settings.get("today_seconds", 0), on_tick_callback=self._on_tick)
        self._update_time_display(self.settings.get("today_seconds", 0))
        self._update_progress(self.settings.get("today_seconds", 0))
        self._update_partner_display()

        # <<< DEĞİŞTİ >>> Ses kontrolü kaldırıldı
        # if self.sound_var.get():
        #     self.toggle_sound()

        # Otomatik döngüleri başlat
        self.auto_fetch_partner()
        self.auto_publish()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # helpers
    def _progress_text(self):
        minutes = self.settings.get("daily_target_minutes", DEFAULT_SETTINGS["daily_target_minutes"])
        done_min = int(self.settings.get("today_seconds", 0) / 60)
        return f"{done_min} / {minutes} dakika"

    def _partner_progress_text(self):
        minutes = self.settings.get("partner_daily_target_minutes", DEFAULT_SETTINGS["daily_target_minutes"])
        done_min = int(self.settings.get("partner_today_seconds", 0) / 60)
        return f"{done_min} / {minutes} dakika"

    def _reward_text(self):
        hearts = self.settings.get("hearts", 0)
        return f"{hearts} kalp topladınız.\nGünde en fazla 1 kalp alabilirsiniz. 💗"

    def _update_time_display(self, total_seconds):
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        self.time_var.set(f"{h:02d}:{m:02d}:{s:02d}")

    def _update_progress(self, total_seconds):
        target_minutes = max(MIN_TARGET_MINUTES, int(self.settings.get("daily_target_minutes", DEFAULT_SETTINGS["daily_target_minutes"])))
        target_seconds = target_minutes * 60
        ratio = min(1.0, total_seconds / target_seconds) if target_seconds > 0 else 0.0
        self.progress.set(ratio)
        self.progress_text.configure(text=self._progress_text())

        # award one heart per day
        today_iso = date.today().isoformat()
        if ratio >= 1.0 and self.settings.get("last_heart_date") != today_iso:
            self.settings["hearts"] = self.settings.get("hearts", 0) + 1
            self.settings["last_heart_date"] = today_iso
            save_settings(self.settings)
            self.lbl_hearts.configure(text="♥ " + str(self.settings["hearts"]))
            self.publish_stats() # Kalp kazanınca veriyi yayınla
            try:
                import tkinter.messagebox as mb
                mb.showinfo("Tebrikler!", "Günlük hedef tamamlandı! 1 kalp kazandın. 💗")
            except Exception:
                pass

    def _update_partner_display(self):
        """Partnerin ilerlemesini ve kalp sayısını arayüzde günceller."""
        target_minutes = max(MIN_TARGET_MINUTES, int(self.settings.get("partner_daily_target_minutes", DEFAULT_SETTINGS["daily_target_minutes"])))
        target_seconds = target_minutes * 60
        partner_seconds = self.settings.get("partner_today_seconds", 0)
        partner_hearts = self.settings.get("partner_hearts", 0)
        ratio = min(1.0, partner_seconds / target_seconds) if target_seconds > 0 else 0.0
        self.partner_progress.set(ratio)
        self.partner_progress_text.configure(text=self._partner_progress_text())
        self.lbl_partner_hearts.configure(text="♥ " + str(partner_hearts))

    def hide_target_error(self):
        self.target_error_label.pack_forget()

    # actions
    def save_target(self):
        try:
            val = int(self.target_var.get())
            self.hide_target_error()
            if val < MIN_TARGET_MINUTES:
                self.target_error_label.pack(pady=(0, 5))
                self.after(5000, self.hide_target_error)
                self.target_var.set(MIN_TARGET_MINUTES)
                self.settings["daily_target_minutes"] = MIN_TARGET_MINUTES
            else:
                self.settings["daily_target_minutes"] = val
            save_settings(self.settings)
            self._update_progress(self.settings.get("today_seconds", 0))
            self.publish_stats() # Yeni hedefi de yayınla
        except Exception:
            import tkinter.messagebox as mb
            mb.showerror("Hata", "Lütfen geçerli bir sayı girin (dakika).")

    def save_note_and_publish(self, event=None):
        """Enter'a basıldığında notu kaydeder ve yayınlar."""
        new_note = self.my_note_var.get()
        self.settings["my_note"] = new_note
        save_settings(self.settings)
        self.publish_stats()
        self.my_note_entry.configure(state="disabled")
        self.after(1000, lambda: self.my_note_entry.configure(state="normal"))
        self.my_note_entry.master.focus()

    def start_timer(self):
        self.timer.start()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

    def stop_timer(self):
        self.timer.stop() # Zamanlayıcıyı durdurur ve _accum_seconds'i günceller
        
        final_seconds = self.timer.get_current_live_seconds()
        self.settings["today_seconds"] = final_seconds
        
        self.settings["saved_date"] = date.today().isoformat()
        save_settings(self.settings)
        self._update_time_display(self.settings["today_seconds"])
        
        # <<< DEĞİŞTİ >>> Stop'a basınca ilerlemeyi ve kalp kontrolünü yap
        self._update_progress(self.settings["today_seconds"])
        
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
        self.publish_stats() # Durunca son veriyi yayınla

    def _on_tick(self, total_seconds):
        self.after(0, lambda: self._update_time_display(total_seconds))
        pass

    # <<< DEĞİŞTİ >>> toggle_sound metodu kaldırıldı.

    def publish_stats(self):
        """Kendi verilerini `share_publish_url` adresine yükler."""
        url = self.settings.get("share_publish_url")
        if not url:
            print("Yayınlama URL'si ayarlanmamış.")
            return

        current_seconds = self.timer.get_current_live_seconds()

        payload = {
            "today_seconds": current_seconds, 
            "hearts": self.settings.get("hearts", 0),
            "last_update": date.today().isoformat(),
            "daily_target": self.settings.get("daily_target_minutes", DEFAULT_SETTINGS["daily_target_minutes"]),
            "note": self.settings.get("my_note", "")
        }

        def _upload():
            try:
                requests.post(url, json=payload, timeout=10) 
                print(f"Veriler yayınlandı: {current_seconds} saniye")
            except Exception as e:
                print(f"Veri yayınlanamadı: {e}")

        threading.Thread(target=_upload, daemon=True).start()

    def auto_publish(self):
        """Her 60 saniyede bir verileri otomatik yayınlar."""
        try:
            if self.timer._running:
                print("Otomatik veri yayınlanıyor (canlı)...")
                self.publish_stats()
        except Exception as e:
            print(f"Auto-publish hatası: {e}")
        finally:
            self.after(60000, self.auto_publish) 

    def fetch_partner_stats(self, is_auto=False):
        """Partner verilerini `partner_fetch_url` adresinden çeker."""
        url = self.settings.get("partner_fetch_url")
        if not url:
            if not is_auto: 
                print("Partner URL'si ayarlanmamış.")
                import tkinter.messagebox as mb
                mb.showerror("Hata", "Partner URL'si ayarlanmamış.\nLütfen 4bbxy_settings.json dosyasını kontrol edin.")
            return

        def _fetch():
            try:
                cache_bust_param = f"?v={int(time.time())}"
                resp = requests.get(url + cache_bust_param, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()

                    today_iso = date.today().isoformat()
                    if data.get("last_update") == today_iso:
                        self.settings["partner_today_seconds"] = data.get("today_seconds", 0)
                    else:
                        self.settings["partner_today_seconds"] = 0
                    
                    self.settings["partner_hearts"] = data.get("hearts", 0)
                    partner_target = data.get("daily_target", 120) 
                    self.settings["partner_daily_target_minutes"] = max(MIN_TARGET_MINUTES, int(partner_target))
                    partner_note = data.get("note", "Partnerin notu...")
                    self.settings["partner_note"] = partner_note
                    
                    save_settings(self.settings)

                    self.after(0, self._update_partner_display)
                    self.after(0, lambda: self.partner_note_label.configure(text="Partner: " + self.settings["partner_note"]))
                else:
                    print(f"Partner verisi alınamadı. Durum Kodu: {resp.status_code}")

            except Exception as e:
                print(f"Partner verisi alınamadı: {e}")
            finally:
                pass

        threading.Thread(target=_fetch, daemon=True).start()

    def auto_fetch_partner(self):
        """Her 60 saniyede bir partner verilerini otomatik olarak çeker."""
        try:
            print("Otomatik partner verisi çekiliyor...")
            self.fetch_partner_stats(is_auto=True)
        except Exception as e:
            print(f"Auto-fetch hatası: {e}")
        finally:
            self.after(60000, self.auto_fetch_partner) 

    def _on_close(self):
        if self.timer._running:
            self.timer.stop() 
        
        final_seconds = self.timer.get_current_live_seconds()
        self.settings["today_seconds"] = final_seconds
        self.settings["saved_date"] = date.today().isoformat()
        
        self.publish_stats()
        save_settings(self.settings)

        time.sleep(0.5)

        # <<< DEĞİŞTİ >>> Kapanışta ambient_player.stop() çağrısı kaldırıldı.
        self.destroy()

# Entry
if __name__ == "__main__":
    app = FourBBXYApp()
    app.mainloop()