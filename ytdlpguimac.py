# yt-dlp Downloader GUI v1.4.14 Mac Edition (by Bluz J & Nai 2026.03.05)
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import datetime
import re
import socket
import shutil
import subprocess
import platform
import sys
import ssl
import certifi

# --- 🍎 Mac 專用：強制修復 SSL 憑證信任鏈 ---
os.environ['SSL_CERT_FILE'] = certifi.where()
ssl._create_default_https_context = ssl._create_unverified_context

# Dependency check
try:
    from yt_dlp import YoutubeDL
except ImportError:
    messagebox.showerror("Error", "Module 'yt-dlp' not found!\nPlease run: pip install yt-dlp")
    sys.exit()

# Core settings and path determination
if getattr(sys, 'frozen', False):
    script_dir = sys._MEIPASS # Mac 打包環境對應
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(os.path.expanduser('~'), ".ytdlpgui_config.json") # Mac 建議將設定檔存在家目錄避免權限問題
HISTORY_FILE = os.path.join(os.path.expanduser('~'), ".ytdlpgui_history.json")
socket.setdefaulttimeout(20)

# Audio Quality Map
AUDIO_QUALITY_MAP = {
    "320 kbps (Best)": "0", "256 kbps": "1", "192 kbps": "2", "140 kbps": "3",
    "128 kbps": "4", "96 kbps": "5",
}
REVERSE_AUDIO_QUALITY_MAP = {v: k for k, v in AUDIO_QUALITY_MAP.items()}

# Global variables
preview_tree = None 
cancel_event, download_thread, loading_animation_id = threading.Event(), None, None
loading_animation_state, last_sort_column, sort_direction = 0, "", "ascending"

# --- I18N Dictionary ---
I18N = {
    "en": {
        "url": "URL:", "analyze": "Analyze", "limit": "Limit (0=All):",
        "type": "Type:", "res": "Res:", "audio": "Audio:", "path": "Path:",
        "browse": "Browse...", "open": "Open", "embed_thumb": "Embed Thumbnail",
        "add_track": "Add Track Num", "save_settings": "Save Settings",
        "dl_subtitles": "Download Subtitles", "preview": "Preview:",
        "refresh": "Refresh", "clear": "Clear", "select_all": "Select All",
        "select_new": "Select New", "download": "Download", "cancel": "Cancel",
        "log": "Log:", "status_analyzing": "Analyzing",
        "msg_select": "Please select items to download.",
        "col_url": "URL", "col_title": "Title", "col_duration": "Duration", "col_lastdl": "Last DL",
        "radio_video": "Video", "radio_audio": "Audio", "radio_cover": "Cover", "radio_subtitle": "Subtitle"
    },
    "zh-TW": {
        "url": "影片網址:", "analyze": "分析", "limit": "解析限制 (0=全部):",
        "type": "格式類型:", "res": "最高畫質:", "audio": "音質:", "path": "儲存路徑:",
        "browse": "瀏覽...", "open": "開啟資料夾", "embed_thumb": "寫入封面圖",
        "add_track": "加入音軌序號", "save_settings": "儲存當前設定",
        "dl_subtitles": "同時下載字幕", "preview": "下載預覽清單:",
        "refresh": "重整紀錄", "clear": "清除選取", "select_all": "全選",
        "select_new": "選取未下載", "download": "開始下載", "cancel": "取消",
        "log": "執行紀錄:", "status_analyzing": "分析中",
        "msg_select": "請選擇要下載的項目。",
        "col_url": "網址", "col_title": "影片標題", "col_duration": "影片時長", "col_lastdl": "最後下載時間",
        "radio_video": "影片", "radio_audio": "純音訊", "radio_cover": "封面圖", "radio_subtitle": "字幕"
    }
}

# Default configuration
config = {
    "download_path": os.path.expanduser('~/Downloads'), 
    "embed_thumbnail": True,
    "video_limit": "1080p", 
    "audio_quality": "320 kbps (Best)", 
    "video_format": "mp4",
    "audio_format": "mp3", 
    "cover_format": "webp",
    "subtitle_format": "srt",
    "download_subtitles_enabled": False,
    "subtitle_language": "zh-TW", 
    "add_track_number": True,
    "url_history": [],
    "playlist_limit": 0,
    "language": "zh-TW"
}

# Load configuration
try:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            loaded_config = json.load(f)
            for key, value in config.items():
                if key not in loaded_config:
                    loaded_config[key] = value
            if 'audio_quality' in loaded_config and loaded_config['audio_quality'].isdigit():
                loaded_config['audio_quality'] = REVERSE_AUDIO_QUALITY_MAP.get(loaded_config['audio_quality'], "320 kbps (Best)")
            config.update(loaded_config)
except (IOError, json.JSONDecodeError) as e: 
    print(f"Error loading config: {e}")

# Load history
download_history = {}
try:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            loaded_history = json.load(f)
            if isinstance(loaded_history, dict): download_history = loaded_history
except Exception as e: print(f"Error loading history: {e}")

def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            temp_config = config.copy()
            if temp_config['audio_quality'] in AUDIO_QUALITY_MAP:
                temp_config['audio_quality'] = AUDIO_QUALITY_MAP[temp_config['audio_quality']]
            if "url_history" in temp_config:
                temp_config["url_history"] = list(dict.fromkeys(temp_config["url_history"]))[:20]
            try: temp_config["playlist_limit"] = int(playlist_limit_spin.get())
            except: temp_config["playlist_limit"] = 0
            temp_config["language"] = current_lang_var.get()
            json.dump(temp_config, f, indent=4, ensure_ascii=False)
    except IOError as e: log_message(f"Error saving config: {e}")

def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(download_history, f, indent=4, ensure_ascii=False)
    except IOError as e: log_message(f"Error saving history: {e}")

def sanitize_filename(filename): return re.sub(r'[\\/:*?"<>|]', '_', filename).strip().rstrip('.')
def log_message(msg): log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n"); log_text.see(tk.END)
def open_folder(path):
    if os.path.exists(path):
        if platform.system() == "Windows": os.startfile(path)
        elif platform.system() == "Darwin": subprocess.Popen(["open", path])
        else: subprocess.Popen(["xdg-open", path])

# --- History Management ---
def add_url_history():
    url = url_combo.get().strip()
    if not url: return
    history = config.get("url_history", [])
    if url in history: history.remove(url)
    history.insert(0, url)
    config["url_history"] = history
    update_url_combo_values()
    save_config()
    log_message(f"URL Saved: {url}")

def delete_url_history():
    url = url_combo.get().strip()
    history = config.get("url_history", [])
    if url in history:
        history.remove(url)
        config["url_history"] = history
        update_url_combo_values()
        url_combo.set("")
        save_config()
        log_message(f"URL Deleted: {url}")

def update_url_combo_values():
    history = config.get("url_history", [])
    url_combo['values'] = history
    if history and not url_combo.get(): url_combo.current(0)

# --- UI Helpers ---
def update_ui_language(*args):
    lang = I18N.get(current_lang_var.get(), I18N["en"])
    lbl_url.config(text=lang["url"]); btn_analyze.config(text=lang["analyze"]); lbl_limit.config(text=lang["limit"])
    lbl_type.config(text=lang["type"]); radio_video.config(text=lang["radio_video"]); radio_audio.config(text=lang["radio_audio"])
    radio_cover.config(text=lang["radio_cover"]); radio_subtitle.config(text=lang["radio_subtitle"]); lbl_res.config(text=lang["res"])
    lbl_audio.config(text=lang["audio"]); lbl_path.config(text=lang["path"]); btn_browse.config(text=lang["browse"])
    btn_open.config(text=lang["open"]); chk_embed.config(text=lang["embed_thumb"]); chk_track.config(text=lang["add_track"])
    btn_save_settings.config(text=lang["save_settings"]); chk_dl_subtitles.config(text=lang["dl_subtitles"])
    lbl_preview.config(text=lang["preview"]); btn_refresh.config(text=lang["refresh"]); btn_clear.config(text=lang["clear"])
    btn_select_all.config(text=lang["select_all"]); btn_select_new.config(text=lang["select_new"])
    download_btn.config(text=lang["download"]); cancel_btn.config(text=lang["cancel"]); lbl_log.config(text=lang["log"])
    for col, key in [("url", "col_url"), ("title", "col_title"), ("duration", "col_duration"), ("last_download", "col_lastdl")]:
        current_text = preview_tree.heading(col, 'text')
        arrow = " 🔽" if "🔽" in current_text else " 🔼" if "🔼" in current_text else ""
        preview_tree.heading(col, text=f"{lang[key]}{arrow}")
    config["language"] = current_lang_var.get(); save_config()

def start_loading_animation():
    global loading_animation_id, loading_animation_state
    lang = I18N.get(current_lang_var.get(), I18N["en"])
    states, loading_animation_state = ["", ".", "..", "..."], (loading_animation_state + 1) % 4
    loading_label.config(text=f"{lang['status_analyzing']}{states[loading_animation_state]}")
    loading_animation_id = root.after(500, start_loading_animation)

def stop_loading_animation():
    global loading_animation_id
    if loading_animation_id: root.after_cancel(loading_animation_id); loading_label.config(text=""); loading_animation_id = None

def update_video_resolution_combo(formats):
    available_heights = sorted(list(set([fmt['height'] for fmt in formats if fmt.get('height') and fmt.get('vcodec') != 'none'])), reverse=True)
    available_resolutions = [f"{h}p" for h in available_heights]
    default_resolutions = ["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
    combined_resolutions = sorted(list(set(default_resolutions + available_resolutions)), key=lambda x: int(x.replace('p', '')), reverse=True)
    video_limit_combo['values'] = combined_resolutions
    current_limit = config.get("video_limit")
    if current_limit in combined_resolutions: video_limit_combo.set(current_limit)
    elif combined_resolutions: video_limit_combo.set(combined_resolutions[0])
    else: video_limit_combo.set("1080p")

def parse_video():
    url = url_combo.get().strip()
    if not url: return log_message("Error: Please enter a URL.")
    add_url_history(); log_message("Analyzing..."); start_loading_animation()
    try: limit_count = int(playlist_limit_spin.get())
    except ValueError: limit_count = 0
        
    def task():
        try:
            ydl_opts = {"quiet": True, "ignoreerrors": True, "extractor_args": {'youtube': ['player_client=default']}}
            if limit_count > 0:
                ydl_opts["playlistend"] = limit_count
                log_message(f"Limit applied: parsing first {limit_count} videos only.")
            if "youtube.com/@" in url and any(x in url for x in ["/videos", "/shorts", "/streams"]):
                log_message("Channel detected, using 'extract_flat' for speed..."); ydl_opts["extract_flat"] = True
                
            with YoutubeDL(ydl_opts) as ydl: info = ydl.extract_info(url, download=False)
            preview_tree.delete(*preview_tree.get_children())
            
            if not info: return log_message("Analysis failed: Invalid URL or network error.")
            if "entries" in info:
                entries = [e for e in info.get("entries", []) if e]
                if not entries: return log_message("No videos found.")
                playlist_title = sanitize_filename(info.get("title", "Unknown Playlist"))
                channel_name = sanitize_filename(info.get("uploader", "Unknown Channel"))
                update_video_resolution_combo(info.get("formats", []))
                for idx, entry in enumerate(entries, start=1):
                    entry['playlist_index'] = entry.get('playlist_index') or idx
                    add_preview_item(idx, entry, "playlist_video", playlist_title, channel_name)
                log_message(f"Analysis complete. Found {len(entries)} items.")
            else:
                channel_name = sanitize_filename(info.get("uploader", "Unknown Channel"))
                add_preview_item(1, info, "video", channel_name=channel_name)
                update_video_resolution_combo(info.get("formats", []))
                log_message("Analysis complete.")
        except Exception as e: log_message(f"Critical error during analysis: {e}")
        finally: stop_loading_animation(); update_subtitle_controls()
    threading.Thread(target=task).start()

def add_preview_item(index, entry, content_type, playlist_title="", channel_name=""):
    video_id, title = entry.get("id", ""), sanitize_filename(entry.get("title", "Unknown"))
    url = entry.get("webpage_url") or entry.get("url") or "N/A"
    duration, duration_text = entry.get("duration"), "Unknown"
    if duration is not None: duration_text = f"{int(duration)//60:02d}:{int(duration)%60:02d}"
    if entry.get("live_status") == "is_upcoming": duration_text = "Upcoming"
    last_download = download_history.get(video_id, "Not Downloaded")
    subtitles = entry.get("subtitles"); available_langs = sorted(list(subtitles.keys())) if subtitles else []
    playlist_index = entry.get('playlist_index', '')
    preview_tree.insert("", tk.END, iid=f"item{index}", values=("☑", url, title, duration_text, last_download, video_id, content_type, playlist_title, channel_name, json.dumps(available_langs), playlist_index))

def toggle_check(event):
    if preview_tree.identify_region(event.x, event.y) == "cell" and preview_tree.identify_column(event.x) == '#1':
        item = preview_tree.identify_row(event.y)
        if item:
            current_value = preview_tree.set(item, "check")
            preview_tree.set(item, "check", "☑" if current_value == "☐" else "☐")
            update_subtitle_controls()

def refresh_history():
    global download_history
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f: download_history = json.load(f)
    except Exception as e: log_message(f"Error refreshing history: {e}"); return
    for item_id in preview_tree.get_children():
        values = list(preview_tree.item(item_id, "values"))
        if values[5] in download_history:
            values[4] = download_history[values[5]]; preview_tree.item(item_id, values=values)
    log_message("History refreshed.")

def select_all():
    for item in preview_tree.get_children(): preview_tree.set(item, "check", "☑")
    update_subtitle_controls()
def deselect_all():
    for item in preview_tree.get_children(): preview_tree.set(item, "check", "☐")
    update_subtitle_controls()
def on_tree_selection_change(event): update_subtitle_controls()
def select_undownloaded():
    for item_id in preview_tree.get_children():
        if preview_tree.item(item_id, "values")[4] == "Not Downloaded": preview_tree.set(item_id, "check", "☑")
    update_subtitle_controls()

def update_subtitle_controls():
    if preview_tree is None: return
    selected_items = [i for i in preview_tree.get_children() if preview_tree.set(i, "check") == "☑"]
    all_sub_langs, has_subtitles = set(), False
    for item_id in selected_items:
        sub_langs_json = preview_tree.item(item_id, "values")[9]
        if sub_langs_json:
            try:
                langs = json.loads(sub_langs_json)
                if langs: has_subtitles = True; all_sub_langs.update(langs)
            except: pass
    
    is_subtitle_mode = download_type_var.get() == "subtitle"
    if has_subtitles:
        subtitle_lang_combo.config(state="readonly")
        lang_values = ["all"] + sorted(list(all_sub_langs))
        subtitle_lang_combo["values"] = lang_values
        current_lang = config["subtitle_language"]
        if current_lang in lang_values: subtitle_lang_combo.set(current_lang)
        elif "zh-TW" in lang_values: subtitle_lang_combo.set("zh-TW")
        elif lang_values: subtitle_lang_combo.set(lang_values[0])
        
        if is_subtitle_mode: chk_dl_subtitles.config(state="disabled"); download_subtitles_var.set(True)
        else: chk_dl_subtitles.config(state="normal")
    else:
        chk_dl_subtitles.config(state="disabled"); download_subtitles_var.set(False)
        subtitle_lang_combo.config(state="disabled"); subtitle_lang_combo.set("")

def select_download_path():
    path = filedialog.askdirectory()
    if path: download_path_entry.delete(0, tk.END); download_path_entry.insert(0, path) 
def open_download_path():
    path = download_path_entry.get().strip()
    if os.path.exists(path): open_folder(path) 
    else: messagebox.showerror("Error", "Path does not exist.")

def save_limit_settings():
    try:
        path = download_path_entry.get().strip()
        config.update({
            "download_path": os.path.normpath(path) if path else os.path.expanduser('~/Downloads'),
            "video_limit": video_limit_combo.get(), "audio_quality": audio_quality_combo.get(),
            "video_format": video_format_combo.get(), "audio_format": audio_format_combo.get(),
            "embed_thumbnail": embed_thumbnail_var.get(), "download_subtitles_enabled": download_subtitles_var.get(),
            "subtitle_language": subtitle_lang_combo.get(), "add_track_number": add_track_number_var.get(),
            "playlist_limit": int(playlist_limit_spin.get()), "language": current_lang_var.get()
        })
        save_config(); log_message("Configuration saved successfully!")
    except Exception as e: log_message(f"Error saving settings: {e}")

def update_format_combobox_visibility(*args):
    download_type = download_type_var.get()
    video_format_combo.pack_forget(); audio_format_combo.pack_forget(); cover_format_combo.pack_forget()
    if download_type == "video": video_format_combo.pack(side="left", padx=5)
    elif download_type == "audio": audio_format_combo.pack(side="left", padx=5)
    elif download_type == "cover": cover_format_combo.pack(side="left", padx=5)
    update_subtitle_controls()

# --- 🍎 Mac 防死鎖對話框 (Thread Safe) ---
gui_event = threading.Event()
gui_result = "replace"
gui_apply_all = False

def _ask_overwrite_ui(filepath):
    global gui_result, gui_apply_all
    temp_result = "replace"
    top = tk.Toplevel(root); top.title("File Exists"); top.geometry("350x150")
    top.attributes('-topmost', True); top.grab_set()
    tk.Label(top, text=f"File already exists:\n{os.path.basename(filepath)}", wraplength=330).pack(pady=5)
    apply_to_all_var = tk.BooleanVar()
    tk.Checkbutton(top, text="Apply to all", variable=apply_to_all_var).pack()
    def on_choice(choice):
        global gui_result, gui_apply_all
        gui_result = choice; gui_apply_all = apply_to_all_var.get()
        gui_event.set(); top.destroy()
    def on_close(): on_choice("skip")
    top.protocol("WM_DELETE_WINDOW", on_close)
    btn_frame = tk.Frame(top); btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="Skip", command=lambda: on_choice("skip")).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Replace", command=lambda: on_choice("replace")).pack(side="left", padx=5)

def ask_overwrite(filepath):
    gui_event.clear()
    root.after(0, lambda: _ask_overwrite_ui(filepath))
    gui_event.wait()
    return gui_result, gui_apply_all
# ------------------------------------------

def start_download_thread():
    global download_thread; download_btn.config(state="disabled"); cancel_btn.config(state="normal")
    cancel_event.clear(); download_thread = threading.Thread(target=download); download_thread.start()

def cancel_download():
    global download_thread; log_message("Cancelling..."); cancel_event.set()
    download_btn.config(state="normal"); cancel_btn.config(state="disabled")

def download():
    download_type = download_type_var.get()
    target_ext = ""
    if download_type == "video": target_ext = video_format_combo.get()
    elif download_type == "audio": target_ext = audio_format_combo.get()
    elif download_type == "subtitle": target_ext = "srt"
    elif download_type == "cover": target_ext = cover_format_combo.get()
    
    ffmpeg_exe = "ffmpeg" # Mac 環境中 FFmpeg 沒有副檔名
    base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else script_dir
    ffmpeg_exe_path = os.path.join(base_path, ffmpeg_exe)

    ydl_opts = {}
    if os.path.exists(ffmpeg_exe_path): ydl_opts['ffmpeg_location'] = ffmpeg_exe_path

    checked_items = [i for i in preview_tree.get_children() if preview_tree.set(i, "check") == "☑"]
    if not checked_items: return log_message(I18N.get(current_lang_var.get(), I18N["en"])["msg_select"])
    
    download_path, total = download_path_entry.get().strip(), len(checked_items)
    overwrite_action = None

    for idx, item in enumerate(checked_items, start=1):
        if cancel_event.is_set(): break
        values = preview_tree.item(item, "values")
        (url, title, video_id, content_type, playlist_title, channel_name, playlist_index) = (
            values[1], values[2], values[5], values[6], values[7], values[8], values[10])
        
        if not url or url == "N/A": continue

        sub_folder = playlist_title if content_type == "playlist_video" else "Videos"
        final_download_path = os.path.join(download_path, channel_name, sub_folder)
        os.makedirs(final_download_path, exist_ok=True) 

        final_title = title
        if add_track_number_var.get() and content_type == "playlist_video" and playlist_index:
            try: final_title = f"{int(playlist_index):02d} - {title}"
            except: pass
        
        base_outtmpl = os.path.join(final_download_path, sanitize_filename(final_title))
        log_message(f"⬇ ({idx}/{total}) Processing: {final_title}")
        
        ydl_opts.update({
            "quiet": True, "progress_hooks": [progress_hook], "noplaylist": True, 
            "outtmpl": f"{base_outtmpl}.%(ext)s", 
            "extractor_args": {'youtube': ['player_client=default']}
        })
        
        pps = []
        if embed_thumbnail_var.get():
            ydl_opts["writethumbnail"] = True
            pps.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'})
            pps.append({'key': 'EmbedThumbnail'})
            pps.append({'key': 'FFmpegMetadata'})

        should_download_sub = (download_type == "subtitle") or (download_subtitles_var.get())
        if should_download_sub:
            selected_lang = subtitle_lang_combo.get()
            ydl_opts.update({"writesubtitles": True, "writeautomaticsub": False, "subtitlesformat": "srt"})
            pps.append({'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'})
            ydl_opts['subtitleslangs'] = [selected_lang] if selected_lang and selected_lang != "all" else ['all', '-live_chat']

        if download_type == "video":
            height_limit = video_limit_combo.get().replace("p", "")
            ydl_opts.update({"format": f"bestvideo[height<={height_limit}]+bestaudio/best", "merge_output_format": target_ext})
        elif download_type == "audio":
            quality_str = audio_quality_combo.get()
            bitrate = re.search(r'(\d+)', quality_str).group(1) if re.search(r'(\d+)', quality_str) else "192"
            ydl_opts.update({"format": "bestaudio/best"})
            pps.append({'key': 'FFmpegExtractAudio', 'preferredcodec': target_ext, 'preferredquality': bitrate})
        elif download_type == "cover":
            ydl_opts.update({"writethumbnail": True, "skip_download": True, "ignoreerrors": True})
            pps.append({'key': 'FFmpegThumbnailsConvertor', 'format': target_ext})
        elif download_type == "subtitle":
            ydl_opts.update({"skip_download": True})

        if pps: ydl_opts["postprocessors"] = pps

        check_filepath = f"{base_outtmpl}.{target_ext}"
        if download_type == "subtitle":
            lang_code = subtitle_lang_combo.get()
            possible_sub = f"{base_outtmpl}.{lang_code}.srt"
            if os.path.exists(possible_sub): check_filepath = possible_sub

        if os.path.exists(check_filepath) and download_type != "subtitle":
            choice = overwrite_action
            if choice is None:
                choice, apply_to_all = ask_overwrite(check_filepath)
                if apply_to_all: overwrite_action = choice
            if choice == "skip": log_message(f"Skipping: {title}"); continue
            elif choice != "replace": log_message("Cancelled."); break
        
        try:
            with YoutubeDL(ydl_opts) as ydl: ydl.download([url])
            log_message(f"Saved: {final_title}")
        except Exception as e: log_message(f"Warning processing '{final_title}': {e}")
        
        download_history[video_id] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_history()

    if not cancel_event.is_set(): log_message("All tasks finished.")
    download_btn.config(state="normal"); cancel_btn.config(state="disabled"); refresh_history()

def progress_hook(d):
    if d["status"] == "downloading":
        try: progress_var.set(float(d.get("_percent_str", "0%").strip().replace("%", "")))
        except ValueError: pass
    elif d["status"] == "finished": progress_var.set(100)

def sort_treeview(column_id):
    global last_sort_column, sort_direction
    if column_id == last_sort_column: sort_direction = "descending" if sort_direction == "ascending" else "ascending"
    else: last_sort_column, sort_direction = column_id, "ascending"
    items = [(preview_tree.set(k, column_id), k) for k in preview_tree.get_children("")]
    def sort_key(item):
        value = item[0]
        if column_id in ("title", "url", "last_download"): return str(value).lower()
        elif column_id == "duration":
            try: m, s = map(int, value.split(':')); return m * 60 + s
            except: return -1
        return value
    items.sort(key=sort_key, reverse=(sort_direction == "descending"))
    for index, (value, k) in enumerate(items): preview_tree.move(k, "", index)
    update_ui_language()

# --- GUI Layout ---
root = tk.Tk()
root.title("yt-dlp Downloader GUI v1.4.14 (Mac Edition)")
root.geometry("980x920")
root.resizable(False, False)

# --- 🍎 Mac 專用：修復 Cmd+C / Cmd+V 複製貼上功能 ---
if platform.system() == "Darwin":
    menubar = tk.Menu(root)
    edit_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Edit", menu=edit_menu)
    edit_menu.add_command(label="Cut", accelerator="Cmd+X", command=lambda: root.focus_get().event_generate("<<Cut>>"))
    edit_menu.add_command(label="Copy", accelerator="Cmd+C", command=lambda: root.focus_get().event_generate("<<Copy>>"))
    edit_menu.add_command(label="Paste", accelerator="Cmd+V", command=lambda: root.focus_get().event_generate("<<Paste>>"))
    edit_menu.add_command(label="Select All", accelerator="Cmd+A", command=lambda: root.focus_get().event_generate("<<SelectAll>>"))
    root.config(menu=menubar)

url_frame = tk.Frame(root)
url_frame.pack(fill="x", padx=10, pady=5)
lbl_url = tk.Label(url_frame, text="URL:")
lbl_url.pack(side="left")

url_combo_frame = tk.Frame(url_frame)
url_combo_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))
url_combo = ttk.Combobox(url_combo_frame, values=[])
url_combo.pack(side="left", fill="x", expand=True)
update_url_combo_values()

tk.Button(url_combo_frame, text="+", command=add_url_history, width=3).pack(side="left", padx=(2,0))
tk.Button(url_combo_frame, text="-", command=delete_url_history, width=3).pack(side="left", padx=(2,0))

lbl_limit = tk.Label(url_frame, text="Limit (0=All):")
lbl_limit.pack(side="left", padx=(10, 2))
playlist_limit_spin = tk.Spinbox(url_frame, from_=0, to=9999, width=5)
playlist_limit_spin.insert(0, config.get("playlist_limit", 0))
playlist_limit_spin.pack(side="left", padx=(0, 5))

btn_analyze = tk.Button(url_frame, text="Analyze", command=parse_video, width=10, height=2)
btn_analyze.pack(side="left", padx=5)

settings_frame = tk.Frame(root)
settings_frame.pack(fill="x", padx=10, pady=5)
download_type_var = tk.StringVar(value=config.get("download_type", "video"))
lbl_type = tk.Label(settings_frame, text="Type:")
lbl_type.pack(side="left")
radio_video = tk.Radiobutton(settings_frame, text="Video", variable=download_type_var, value="video", command=update_format_combobox_visibility)
radio_video.pack(side="left", padx=(10, 0))
radio_audio = tk.Radiobutton(settings_frame, text="Audio", variable=download_type_var, value="audio", command=update_format_combobox_visibility)
radio_audio.pack(side="left", padx=5)
radio_cover = tk.Radiobutton(settings_frame, text="Cover", variable=download_type_var, value="cover", command=update_format_combobox_visibility)
radio_cover.pack(side="left", padx=5)
radio_subtitle = tk.Radiobutton(settings_frame, text="Subtitle", variable=download_type_var, value="subtitle", command=update_format_combobox_visibility)
radio_subtitle.pack(side="left", padx=5)

tk.Label(settings_frame, text=" | ").pack(side="left")
lbl_res = tk.Label(settings_frame, text="Res:")
lbl_res.pack(side="left")
video_limit_combo = ttk.Combobox(settings_frame, values=["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"], width=7, state="readonly")
video_limit_combo.set(config["video_limit"])
video_limit_combo.pack(side="left", padx=5)
lbl_audio = tk.Label(settings_frame, text="Audio:")
lbl_audio.pack(side="left")
audio_quality_combo = ttk.Combobox(settings_frame, values=list(AUDIO_QUALITY_MAP.keys()), width=15, state="readonly")
audio_quality_combo.set(config["audio_quality"])
audio_quality_combo.pack(side="left", padx=5)
video_format_combo = ttk.Combobox(settings_frame, values=["mp4", "mkv"], width=5, state="readonly")
video_format_combo.set(config["video_format"])
audio_format_combo = ttk.Combobox(settings_frame, values=["mp3", "m4a"], width=5, state="readonly")
audio_format_combo.set(config["audio_format"])
cover_format_combo = ttk.Combobox(settings_frame, values=["webp"], width=5, state="readonly")
cover_format_combo.set("webp")

path_frame = tk.Frame(root)
path_frame.pack(fill="x", padx=10)
lbl_path = tk.Label(path_frame, text="Path:")
lbl_path.pack(side="left")
download_path_entry = tk.Entry(path_frame)
download_path_entry.insert(0, config["download_path"])
download_path_entry.pack(side="left", fill="x", expand=True)
btn_browse = tk.Button(path_frame, text="Browse...", command=select_download_path)
btn_browse.pack(side="left", padx=5)
btn_open = tk.Button(path_frame, text="Open", command=open_download_path)
btn_open.pack(side="left", padx=5)

options_frame = tk.Frame(root)
options_frame.pack(fill="x", padx=10, pady=5, anchor="w")
embed_thumbnail_var = tk.BooleanVar(value=config["embed_thumbnail"])
chk_embed = tk.Checkbutton(options_frame, text="Embed Thumbnail", variable=embed_thumbnail_var)
chk_embed.pack(side="left")
add_track_number_var = tk.BooleanVar(value=config.get("add_track_number", True))
chk_track = tk.Checkbutton(options_frame, text="Add Track Num", variable=add_track_number_var)
chk_track.pack(side="left", padx=(10, 0))
btn_save_settings = tk.Button(options_frame, text="Save Settings", command=save_limit_settings)
btn_save_settings.pack(side="right")

subtitles_frame = tk.Frame(root)
subtitles_frame.pack(fill="x", padx=10, pady=(0,5), anchor="w")
download_subtitles_var = tk.BooleanVar(value=config["download_subtitles_enabled"])
chk_dl_subtitles = tk.Checkbutton(subtitles_frame, text="Download Subtitles", variable=download_subtitles_var, state="disabled")
chk_dl_subtitles.pack(side="left")
subtitle_lang_combo = ttk.Combobox(subtitles_frame, values=[], width=10, state="disabled")
subtitle_lang_combo.set(config["subtitle_language"])
subtitle_lang_combo.pack(side="left", padx=5)
loading_label = tk.Label(subtitles_frame, text="", width=15)
loading_label.pack(side="left", padx=5)

preview_frame = tk.Frame(root)
preview_frame.pack(fill="both", expand=True, padx=10)
preview_control_frame = tk.Frame(preview_frame)
preview_control_frame.pack(fill="x")
lbl_preview = tk.Label(preview_control_frame, text="Preview:")
lbl_preview.pack(side="left", pady=(5,0))
btn_refresh = tk.Button(preview_control_frame, text="Refresh", command=refresh_history)
btn_refresh.pack(side="right", padx=(5, 0), pady=(5,0))
btn_clear = tk.Button(preview_control_frame, text="Clear", command=deselect_all)
btn_clear.pack(side="right", padx=5, pady=(5,0))
btn_select_all = tk.Button(preview_control_frame, text="Select All", command=select_all)
btn_select_all.pack(side="right", padx=5, pady=(5,0))
btn_select_new = tk.Button(preview_control_frame, text="Select New", command=select_undownloaded)
btn_select_new.pack(side="right", padx=5, pady=(5,0))

columns = ("check", "url", "title", "duration", "last_download", "video_id", "content_type", "playlist_title", "channel_name", "subtitles", "playlist_index")
preview_tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=15)
preview_tree.heading("check", text="✓")
preview_tree.heading("url", text="URL")
preview_tree.heading("title", text="Title", command=lambda: sort_treeview("title"))
preview_tree.heading("duration", text="Duration", command=lambda: sort_treeview("duration"))
preview_tree.heading("last_download", text="Last DL", command=lambda: sort_treeview("last_download"))
preview_tree.column("check", width=30, anchor="center", stretch=False)
preview_tree.column("url", width=150, stretch=False)
preview_tree.column("title", width=350)
preview_tree.column("duration", width=70, anchor="center", stretch=False)
preview_tree.column("last_download", width=120, anchor="center", stretch=False)
for col in ["video_id", "content_type", "playlist_title", "channel_name", "subtitles", "playlist_index"]: preview_tree.column(col, width=0, stretch=tk.NO)
preview_tree.pack(fill="both", expand=True, pady=5)
preview_tree.bind("<Button-1>", toggle_check)
preview_tree.bind("<KeyRelease-space>", lambda e: [preview_tree.set(i, "check", "☑" if preview_tree.set(i, "check") == "☐" else "☐") for i in preview_tree.selection()] and update_subtitle_controls())
preview_tree.bind("<<TreeviewSelect>>", on_tree_selection_change)

progress_frame = tk.Frame(root)
progress_frame.pack(fill="x", padx=10, pady=5)
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
progress_bar.pack(side="left", fill="x", expand=True)
download_btn = tk.Button(progress_frame, text="Download", command=start_download_thread, width=10, height=2)
download_btn.pack(side="left", padx=(5, 0))
cancel_btn = tk.Button(progress_frame, text="Cancel", command=cancel_download, width=10, height=2, state="disabled")
cancel_btn.pack(side="left", padx=(5, 0))

log_frame = tk.Frame(root)
log_frame.pack(fill="both", expand=True, padx=10, pady=5)

log_top_frame = tk.Frame(log_frame)
log_top_frame.pack(fill="x")
lbl_log = tk.Label(log_top_frame, text="Log:")
lbl_log.pack(side="left")

current_lang_var = tk.StringVar(value=config.get("language", "zh-TW"))
lang_combo = ttk.Combobox(log_top_frame, textvariable=current_lang_var, values=["en", "zh-TW"], width=7, state="readonly")
lang_combo.pack(side="right")
lang_combo.bind("<<ComboboxSelected>>", update_ui_language)

log_text = tk.Text(log_frame, height=8)
log_text.pack(fill="both", expand=True, pady=5)

update_format_combobox_visibility()
update_ui_language()

root.mainloop()