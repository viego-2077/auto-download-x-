import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import shutil
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class XDownloaderToggleMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("X Video Downloader - 2077 - Motion")
        self.geometry("750x780")
        ctk.set_appearance_mode("dark")

        self.is_running = False
        self.stop_requested = False
        self.monitor_enabled = tk.BooleanVar(value=True) 
        self.last_clipboard_content = ""

        ctk.CTkLabel(self, text="DANH SÁCH LINK X", font=("Arial", 16, "bold"), text_color="#1DA1F2").pack(pady=(20, 5))
        
        self.textbox_links = ctk.CTkTextbox(self, width=650, height=200, border_width=2, border_color="#1DA1F2")
        self.textbox_links.pack(pady=10)

        self.monitor_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.monitor_frame.pack(pady=5)

        self.switch_monitor = ctk.CTkSwitch(self.monitor_frame, text="Tự động nhận diện link từ Clipboard", 
                                            variable=self.monitor_enabled, onvalue=True, offvalue=False,
                                            progress_color="#1DA1F2", command=self.update_monitor_status)
        self.switch_monitor.pack(side="left", padx=10)

        self.btn_clear = ctk.CTkButton(self, text="Xóa danh sách", width=120, 
                                       fg_color="#6c757d", hover_color="#5a6268", command=self.clear_links)
        self.btn_clear.pack(pady=5)

        self.path_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.path_frame.pack(pady=15)
        self.entry_path = ctk.CTkEntry(self.path_frame, width=480)
        default_path = os.path.join(os.path.expanduser("~"), "Desktop", "video")
        self.entry_path.insert(0, default_path)
        self.entry_path.pack(side="left", padx=5)
        ctk.CTkButton(self.path_frame, text="Chọn Thư Mục", width=120, command=self.browse_folder).pack(side="left")

        self.btn_action = ctk.CTkButton(self, text="BẮT ĐẦU TẢI VIDEO", fg_color="#1DA1F2", hover_color="#1991db", 
                                       font=("Arial", 14, "bold"), height=50, command=self.handle_action)
        self.btn_action.pack(pady=10)

        self.terminal_log = ctk.CTkTextbox(self, width=650, height=180, fg_color="#000000", text_color="#00FF00", font=("Consolas", 12))
        self.terminal_log.pack(pady=5)
        self.terminal_log.configure(state="disabled")

        threading.Thread(target=self.clipboard_monitor_thread, daemon=True).start()

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.terminal_log.configure(state="normal")
        self.terminal_log.insert("end", f"[{timestamp}] {message}\n")
        self.terminal_log.configure(state="disabled")
        self.terminal_log.see("end")

    def update_monitor_status(self):
        status = "BẬT" if self.monitor_enabled.get() else "TẮT"
        self.log(f"Chế độ theo dõi Clipboard: {status}")

    def clipboard_monitor_thread(self):
        while True:
            if self.monitor_enabled.get():
                try:
                    content = self.clipboard_get().strip()
                    if content and content != self.last_clipboard_content:
                        self.last_clipboard_content = content
                        pattern = r'https?://(?:x\.com|twitter\.com)/[a-zA-Z0-9_]+/status/\d+'
                        found_links = re.findall(pattern, content)
                        
                        if found_links:
                            existing_text = self.textbox_links.get("1.0", tk.END).strip()
                            added_count = 0
                            for link in found_links:
                                if link not in existing_text:
                                    if existing_text == "":
                                        self.textbox_links.insert(tk.END, link)
                                        existing_text = link
                                    else:
                                        self.textbox_links.insert(tk.END, "\n" + link)
                                    added_count += 1
                            if added_count > 0:
                                self.log(f"Đã dán {added_count} link mới từ Clipboard.")
                except Exception:
                    pass
            time.sleep(1.5)

    def clear_links(self):
        self.textbox_links.delete("1.0", tk.END)
        self.log("Đã xóa danh sách.")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, folder)

    def handle_action(self):
        if not self.is_running: self.start_process()
        else: self.stop_process()

    def start_process(self):
        self.is_running = True
        self.stop_requested = False
        self.btn_action.configure(text="DỪNG TẢI NGAY", fg_color="#CC0000", hover_color="#990000")
        threading.Thread(target=self.run_logic, daemon=True).start()

    def stop_process(self):
        self.stop_requested = True
        self.log("!!! ĐANG DỪNG HỆ THỐNG !!!")
        self.btn_action.configure(state="disabled", text="ĐANG DỪNG...")

    def run_logic(self):
        links_raw = self.textbox_links.get("1.0", tk.END).strip().split('\n')
        links = [l.strip() for l in links_raw if l.strip()]
        save_dir = os.path.abspath(self.entry_path.get())
        
        if not os.path.exists(save_dir): os.makedirs(save_dir)
        if not links:
            messagebox.showwarning("Lỗi", "Danh sách trống!")
            self.reset_ui()
            return

        edge_options = Options()
        user_data_dir = os.path.join(os.getcwd(), "2077_dep_trai")
        edge_options.add_argument(f"user-data-dir={user_data_dir}")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--start-minimized")
        
        prefs = {"download.default_directory": save_dir, "download.prompt_for_download": False}
        edge_options.add_experimental_option("prefs", prefs)

        driver = None
        try:
            self.log("Khởi tạo Edge...")
            driver = webdriver.Edge(options=edge_options)
            
            for index, link in enumerate(links):
                if self.stop_requested: break
                self.log(f"Đang tải video {index+1}/{len(links)}...")
                try:
                    driver.get("https://sssx.io/")
                    wait = WebDriverWait(driver, 20)
                    input_el = wait.until(EC.element_to_be_clickable((By.ID, "main_page_text")))
                    input_el.clear()
                    input_el.send_keys(link)
                    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "submit"))
                    dl_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'download')]")))
                    driver.execute_script("arguments[0].click();", dl_btn)
                    
                    self.log(f"==> OK.")
                    time.sleep(12)
                except Exception:
                    self.log(f"Lỗi link thứ {index+1}")
                    continue

            if not self.stop_requested:
                self.log("Đợi hoàn tất tải xuống...")
                while any(f.endswith('.crdownload') for f in os.listdir(save_dir)):
                    if self.stop_requested: break
                    time.sleep(2)

        except Exception as e: self.log(f"LỖI: {str(e)[:50]}")
        finally:
            if driver: driver.quit()
            try: shutil.rmtree(user_data_dir, ignore_errors=True)
            except: pass
            self.reset_ui()

    def reset_ui(self):
        self.is_running = False
        self.btn_action.configure(state="normal", text="BẮT ĐẦU TẢI VIDEO", fg_color="#1DA1F2", hover_color="#1991db")
        self.log("--- SẴN SÀNG ---")

if __name__ == "__main__":
    app = XDownloaderToggleMonitor()
    app.mainloop()