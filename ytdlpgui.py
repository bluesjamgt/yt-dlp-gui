# yt-dlp Downloader GUI v1.4.11x (by Bluz J & Nai 2026.01.02)
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

# Dependency check
try:
    from yt_dlp import YoutubeDL
except ImportError:
    messagebox.showerror("Error", "Module 'yt-dlp' not found!\nPlease run: pip install yt-dlp")
    sys.exit()

# Core settings and path determination
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(script_dir, "config.json")
HISTORY_FILE = os.path.join(script_dir, "download_history.json")
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

# Default configuration
config = {
    "download_path": os.path.expanduser('~/Downloads'), 
    "embed_thumbnail": True,
    "video_limit": "1440p", 
    "audio_quality": "320 kbps (Best)", 
    "video_format": "mp4",
    "audio_format": "mp3", 
    "cover_format": "webp",
    "subtitle_format": "srt",
    "download_subtitles_enabled": False,
    "subtitle_language": "en", 
    "add_track_number": True,
    "url_history": [],
    "playlist_limit": 0 
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
            if isinstance(loaded_history, dict):
                download_history = loaded_history
except Exception as e:
    print(f"Error loading history: {e}")

def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            temp_config = config.copy()
            if temp_config['audio_quality'] in AUDIO_QUALITY_MAP:
                temp_config['audio_quality'] = AUDIO_QUALITY_MAP[temp_config['audio_quality']]
            
            if "url_history" in temp_config:
                temp_config["url_history"] = list(dict.fromkeys(temp_config["url_history"]))[:20]
            
            try:
                temp_config["playlist_limit"] = int(playlist_limit_spin.get())
            except:
                temp_config["playlist_limit"] = 0

            json.dump(temp_config, f, indent=4)
    except IOError as e:
        log_message(f"Error saving config: {e}")

def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(download_history, f, indent=4)
    except IOError as e:
        log_message(f"Error saving history: {e}")

def sanitize_filename(filename):
    s = re.sub(r'[\\/:*?"<>|]', '_', filename)
    return s.strip().rstrip('.')

def log_message(msg): 
    log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")
    log_text.see(tk.END)

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
    else:
        log_message("URL not found in history.")

def update_url_combo_values():
    history = config.get("url_history", [])
    url_combo['values'] = history
    if history and not url_combo.get(): url_combo.current(0)

# --- UI Helpers ---

def start_loading_animation():
    global loading_animation_id, loading_animation_state
    states, loading_animation_state = ["", ".", "..", "..."], (loading_animation_state + 1) % 4
    loading_label.config(text=f"Analyzing{states[loading_animation_state]}")
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
    add_url_history()
    log_message("Analyzing..."); start_loading_animation()
    
    try:
        limit_count = int(playlist_limit_spin.get())
    except ValueError:
        limit_count = 0
        
    def task():
        try:
            ydl_opts = {
                "quiet": True, 
                "ignoreerrors": True,
                "extractor_args": {'youtube': ['player_client=default']}
            }
            
            if limit_count > 0:
                ydl_opts["playlistend"] = limit_count
                log_message(f"Limit applied: parsing first {limit_count} videos only.")

            if "youtube.com/@" in url and any(x in url for x in ["/videos", "/shorts", "/streams"]):
                log_message("Channel detected, using 'extract_flat' for speed...")
                ydl_opts["extract_flat"] = True
                
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
                add_preview_item(1, info, "video", channel_name=sanitize_filename(info.get("uploader", "Unknown Channel")))
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
    
    if entry.get("live_status") == "is_upcoming":
        duration_text = "Upcoming"
        
    last_download = download_history.get(video_id, "Not Downloaded")
    subtitles = entry.get("subtitles")
    available_langs = sorted(list(subtitles.keys())) if subtitles else []
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
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                download_history = json.load(f)
        else:
            download_history = {}
    except (IOError, json.JSONDecodeError) as e:
        log_message(f"Error refreshing history: {e}")
        return

    for item_id in preview_tree.get_children():
        values = list(preview_tree.item(item_id, "values"))
        video_id = values[5]
        if video_id in download_history:
            values[4] = download_history[video_id]
            preview_tree.item(item_id, values=values)
    log_message("History refreshed.")

def select_all():
    for item in preview_tree.get_children(): preview_tree.set(item, "check", "☑")
    update_subtitle_controls()
def deselect_all():
    for item in preview_tree.get_children(): preview_tree.set(item, "check", "☐")
    update_subtitle_controls()
def on_tree_selection_change(event): update_subtitle_controls()

def update_subtitle_controls():
    if preview_tree is None: return

    selected_items = [i for i in preview_tree.get_children() if preview_tree.set(i, "check") == "☑"]
    all_sub_langs, has_subtitles = set(), False
    for item_id in selected_items:
        values = preview_tree.item(item_id, "values"); sub_langs_json = values[9]
        if sub_langs_json:
            try:
                langs = json.loads(sub_langs_json)
                if langs: has_subtitles = True; all_sub_langs.update(langs)
            except json.JSONDecodeError: pass
    
    is_subtitle_mode = download_type_var.get() == "subtitle"
    
    if has_subtitles:
        subtitle_lang_combo.config(state="readonly")
        lang_values = ["all"] + sorted(list(all_sub_langs))
        subtitle_lang_combo["values"] = lang_values
        current_lang = config["subtitle_language"]
        if current_lang in lang_values: subtitle_lang_combo.set(current_lang)
        elif "zh-TW" in lang_values: subtitle_lang_combo.set("zh-TW")
        elif lang_values: subtitle_lang_combo.set(lang_values[0])
        else: subtitle_lang_combo.set("all")
        
        if is_subtitle_mode:
             download_subtitles_check.config(state="disabled") 
             download_subtitles_var.set(True)
        else:
             download_subtitles_check.config(state="normal")
             
    else:
        download_subtitles_check.config(state="disabled"); download_subtitles_var.set(False)
        subtitle_lang_combo.config(state="disabled"); subtitle_lang_combo.set("")

def set_default_path():
    default_path = os.path.expanduser('~/Downloads')
    download_path_entry.delete(0, tk.END); download_path_entry.insert(0, default_path)
    log_message("Path set to default Downloads folder.")

def select_download_path():
    path = filedialog.askdirectory()
    if path:  
        download_path_entry.delete(0, tk.END)  
        download_path_entry.insert(0, path)    
def save_download_path():
    path = download_path_entry.get().strip()
    if path:
        config["download_path"] = os.path.normpath(path)
        save_config()
        log_message("Path saved.")
    else:
        log_message("Error: Path cannot be empty.")

def open_download_path():
    path = download_path_entry.get().strip()
    if os.path.exists(path): open_folder(path) 
    else: messagebox.showerror("Error", "Path does not exist.")

def save_limit_settings():
    try:
        path = download_path_entry.get().strip()
        config.update({
            "download_path": os.path.normpath(path) if path else os.path.expanduser('~/Downloads'),
            "video_limit": video_limit_combo.get(),
            "audio_quality": audio_quality_combo.get(),
            "video_format": video_format_combo.get(),
            "audio_format": audio_format_combo.get(),
            "embed_thumbnail": embed_thumbnail_var.get(),
            "download_subtitles_enabled": download_subtitles_var.get(),
            "subtitle_language": subtitle_lang_combo.get(),
            "add_track_number": add_track_number_var.get(),
            "playlist_limit": int(playlist_limit_spin.get()) 
        })
        save_config() 
        log_message("Configuration saved successfully!")
    except Exception as e:
        log_message(f"Error saving settings: {e}")

def update_format_combobox_visibility(*args):
    download_type = download_type_var.get()
    video_format_combo.pack_forget(); audio_format_combo.pack_forget(); cover_format_combo.pack_forget()
    if download_type == "video": video_format_combo.pack(side="left", padx=5)
    elif download_type == "audio": audio_format_combo.pack(side="left", padx=5)
    elif download_type == "cover": cover_format_combo.pack(side="left", padx=5)
    
    update_subtitle_controls()

def ask_overwrite(filepath):
    result, apply_to_all = "replace", False
    top = tk.Toplevel(root); top.title("File Exists"); top.geometry("350x150"); top.grab_set()
    tk.Label(top, text=f"File already exists:\n{os.path.basename(filepath)}", wraplength=330).pack(pady=5)
    apply_to_all_var = tk.BooleanVar()
    tk.Checkbutton(top, text="Apply to all", variable=apply_to_all_var).pack()
    def on_choice(choice): nonlocal result, apply_to_all; result = choice; apply_to_all = apply_to_all_var.get(); top.destroy()
    btn_frame = tk.Frame(top); btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="Skip", command=lambda: on_choice("skip")).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Replace", command=lambda: on_choice("replace")).pack(side="left", padx=5)
    root.wait_window(top)
    return result, apply_to_all

def start_download_thread():
    global download_thread; download_btn.config(state="disabled"); cancel_btn.config(state="normal")
    cancel_event.clear(); download_thread = threading.Thread(target=download); download_thread.start()

def cancel_download():
    global download_thread; log_message("Cancelling..."); cancel_event.set()
    if download_thread and download_thread.is_alive(): download_thread.join()
    download_btn.config(state="normal"); cancel_btn.config(state="disabled"); log_message("Download cancelled.")

def toggle_check_with_space(event):
    for item_id in preview_tree.selection():
        current_value = preview_tree.set(item_id, "check")
        preview_tree.set(item_id, "check", "☑" if current_value == "☐" else "☐")
    update_subtitle_controls()

def select_undownloaded():
    for item_id in preview_tree.get_children():
        values = preview_tree.item(item_id, "values")
        last_download_status = values[4]
        if last_download_status == "Not Downloaded":
            preview_tree.set(item_id, "check", "☑")
    update_subtitle_controls()


def download():
    download_type = download_type_var.get()
    
    target_ext = ""
    if download_type == "video": target_ext = video_format_combo.get()
    elif download_type == "audio": target_ext = audio_format_combo.get()
    elif download_type == "subtitle": target_ext = "srt"
    
    ffmpeg_exe_path = 'ffmpeg'
    ydl_opts = {}

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        ffmpeg_exe_path = os.path.join(sys._MEIPASS, 'ffmpeg.exe')
        ydl_opts['ffmpeg_location'] = sys._MEIPASS

    needs_ffmpeg = target_ext in ["mp3", "mkv", "srt"]
    if needs_ffmpeg and not shutil.which(ffmpeg_exe_path.replace('.exe','')):
        log_message(f"Warning: ffmpeg not found! Conversion might fail.")

    checked_items = [i for i in preview_tree.get_children() if preview_tree.set(i, "check") == "☑"]
    if not checked_items: return log_message("Please select items to download.")
    
    download_path, total = download_path_entry.get().strip(), len(checked_items)
    overwrite_action = None

    for idx, item in enumerate(checked_items, start=1):
        if cancel_event.is_set(): break
        values = preview_tree.item(item, "values")
        (url, title, video_id, content_type, playlist_title, 
         channel_name, playlist_index) = (values[1], values[2], values[5], values[6], 
                                          values[7], values[8], values[10])
        
        if not url or url == "N/A": log_message(f"Skipping '{title}' (No URL)."); continue

        # --- Folder Structure ---
        sub_folder = playlist_title if content_type == "playlist_video" else "Videos"
        final_download_path = os.path.join(download_path, channel_name, sub_folder)
        if not os.path.exists(final_download_path): os.makedirs(final_download_path)

        final_title = title
        if add_track_number_var.get() and content_type == "playlist_video" and playlist_index:
            try: final_title = f"{int(playlist_index):02d} - {title}"
            except (ValueError, TypeError): pass
        
        base_outtmpl = os.path.join(final_download_path, final_title)
        
        temp_ext = ""
        log_message(f"⬇ ({idx}/{total}) Processing: {final_title}")
        
        ydl_opts.update({
            "quiet": True, 
            "progress_hooks": [progress_hook], 
            "noplaylist": True, 
            "outtmpl": base_outtmpl,
            "extractor_args": {'youtube': ['player_client=default']}
        })
        
        pps_common = []
        if embed_thumbnail_var.get():
             ydl_opts["writethumbnail"] = True
             pps_common.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'})
             ydl_opts["addmetadata"] = True

        should_download_sub = (download_type == "subtitle") or (download_subtitles_var.get())
        
        if should_download_sub:
             selected_lang = subtitle_lang_combo.get()
             ydl_opts.update({
                 "writesubtitles": True,
                 "writeautomaticsub": False,
                 "subtitlesformat": "srt",
                 "postprocessors": [{'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'}]
             })
             if selected_lang and selected_lang != "all":
                 ydl_opts['subtitleslangs'] = [selected_lang]
             else:
                 ydl_opts['subtitleslangs'] = ['all', '-live_chat']

        if download_type == "video":
            temp_ext = "mp4"
            height_limit = video_limit_combo.get().replace("p", "")
            ydl_opts.update({"format": f"bestvideo[height<={height_limit}]+bestaudio/best[height<={height_limit}]", "merge_output_format": temp_ext})
            
            if embed_thumbnail_var.get():
                pps_common.append({'key': 'EmbedThumbnail'})
                pps_common.append({'key': 'FFmpegMetadata'})
            
            if pps_common:
                ydl_opts.update({"postprocessors": pps_common})

        elif download_type == "audio":
            temp_ext = "m4a"
            audio_pps = []
            if embed_thumbnail_var.get():
                audio_pps.extend(pps_common)
                audio_pps.append({'key': 'EmbedThumbnail'})
                
            audio_pps.append({'key': 'FFmpegExtractAudio', 'preferredcodec': temp_ext})
            
            if embed_thumbnail_var.get():
                audio_pps.append({'key': 'FFmpegMetadata'})
                
            ydl_opts.update({"format": "bestaudio/best", "postprocessors": audio_pps})


        elif download_type == "cover":
            target_ext, temp_ext = cover_format_combo.get(), cover_format_combo.get()
            ydl_opts.update({
                "writethumbnail": True, 
                "skip_download": True, 
                "ignoreerrors": True, 
                "postprocessors": [{'key': 'FFmpegThumbnailsConvertor', 'format': temp_ext}]
            })
        
        elif download_type == "subtitle":
            ydl_opts.update({"skip_download": True})
            target_ext = "srt"
            temp_ext = "srt"

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
        except Exception as e:
            log_message(f"Warning processing '{final_title}': {e}")
        
        if download_type in ["video", "audio"]:
            temp_filepath = f"{base_outtmpl}.{temp_ext}"
            final_filepath = f"{base_outtmpl}.{target_ext}"
            
            if not os.path.exists(temp_filepath):
                 if os.path.exists(final_filepath):
                     temp_filepath = final_filepath
                 else:
                    if os.path.exists(f"{base_outtmpl}.webm"): temp_filepath = f"{base_outtmpl}.webm"
                    else: log_message(f"Warning: Primary file not found (could be merged)."); continue

            if temp_ext != target_ext:
                log_message(f"Converting {temp_ext} to {target_ext}...")
                ffmpeg_cmd = []
                if target_ext == "mkv":
                    ffmpeg_cmd = [ffmpeg_exe_path, '-y', '-i', temp_filepath, '-codec', 'copy', final_filepath]
                elif target_ext == "mp3":
                    quality_str = audio_quality_combo.get()
                    bitrate = re.search(r'(\d+)', quality_str).group(1) if re.search(r'(\d+)', quality_str) else "192"
                    ffmpeg_cmd = [ffmpeg_exe_path, '-y', '-i', temp_filepath, '-vn', '-codec:a', 'libmp3lame', '-b:a', f'{bitrate}k', final_filepath]

                if ffmpeg_cmd:
                    try:
                        startupinfo = None
                        if platform.system() == "Windows":
                            startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        subprocess.run(ffmpeg_cmd, check=True, startupinfo=startupinfo, capture_output=True)
                        log_message(f"Conversion successful.")
                        if os.path.exists(temp_filepath) and temp_filepath != final_filepath:
                             os.remove(temp_filepath)
                    except (subprocess.CalledProcessError, FileNotFoundError) as e:
                        log_message(f"FFmpeg conversion failed! Keeping original format.")
            else:
                if temp_filepath != final_filepath and os.path.exists(temp_filepath):
                    os.rename(temp_filepath, final_filepath)
            
            log_message(f"Saved to: {final_filepath}")
        
        elif download_type == "subtitle":
             log_message(f"Subtitle download requested.")
        
        elif download_type == "cover":
             final_cover_path = f"{base_outtmpl}.{target_ext}"
             if os.path.exists(final_cover_path):
                 log_message(f"Cover downloaded.")
             else:
                 log_message(f"Cover process finished.")


        download_history[video_id] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_history()

    if not cancel_event.is_set(): log_message("All tasks finished.")
    download_btn.config(state="normal"); cancel_btn.config(state="disabled")
    refresh_history()

def progress_hook(d):
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "0%").strip()
        try: progress_var.set(float(percent.replace("%", "")))
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
    for col in preview_tree["columns"]:
        heading_text = preview_tree.heading(col, 'text').replace(' 🔽', '').replace(' 🔼', '')
        if col == column_id:
            arrow = " 🔽" if sort_direction == "descending" else " 🔼"
            preview_tree.heading(col, text=f"{heading_text}{arrow}")
        else: preview_tree.heading(col, text=heading_text)

# --- GUI Layout ---
root = tk.Tk()
root.title("yt-dlp Downloader GUI v1.4.11x (2026.01.02)")
root.geometry("980x920")
root.resizable(False, False)

# URL Input Area
url_frame = tk.Frame(root)
url_frame.pack(fill="x", padx=10, pady=5)
tk.Label(url_frame, text="URL:").pack(side="left")

url_combo_frame = tk.Frame(url_frame)
url_combo_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))
url_combo = ttk.Combobox(url_combo_frame, values=[])
url_combo.pack(side="left", fill="x", expand=True)
update_url_combo_values()

tk.Button(url_combo_frame, text="+", command=add_url_history, width=3).pack(side="left", padx=(2,0))
tk.Button(url_combo_frame, text="-", command=delete_url_history, width=3).pack(side="left", padx=(2,0))

# Playlist Limit
tk.Label(url_frame, text="Limit (0=All):").pack(side="left", padx=(10, 2))
playlist_limit_spin = tk.Spinbox(url_frame, from_=0, to=9999, width=5)
playlist_limit_spin.delete(0, "end")
playlist_limit_spin.insert(0, config.get("playlist_limit", 0))
playlist_limit_spin.pack(side="left", padx=(0, 5))

tk.Button(url_frame, text="Analyze", command=parse_video, width=10, height=2).pack(side="left", padx=5)

# Settings Area
settings_frame = tk.Frame(root)
settings_frame.pack(fill="x", padx=10, pady=5)
download_type_var = tk.StringVar(value=config.get("download_type", "video"))
tk.Label(settings_frame, text="Type:").pack(side="left")
tk.Radiobutton(settings_frame, text="Video", variable=download_type_var, value="video", command=update_format_combobox_visibility).pack(side="left", padx=(10, 0))
tk.Radiobutton(settings_frame, text="Audio", variable=download_type_var, value="audio", command=update_format_combobox_visibility).pack(side="left", padx=5)
tk.Radiobutton(settings_frame, text="Cover", variable=download_type_var, value="cover", command=update_format_combobox_visibility).pack(side="left", padx=5)
tk.Radiobutton(settings_frame, text="Subtitle", variable=download_type_var, value="subtitle", command=update_format_combobox_visibility).pack(side="left", padx=5)

tk.Label(settings_frame, text=" | ").pack(side="left")
tk.Label(settings_frame, text="Res:").pack(side="left")
video_limit_combo = ttk.Combobox(settings_frame, values=["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"], width=7, state="readonly")
video_limit_combo.set(config["video_limit"])
video_limit_combo.pack(side="left", padx=5)
tk.Label(settings_frame, text="Audio:").pack(side="left")
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
tk.Label(path_frame, text="Path:").pack(side="left")
download_path_entry = tk.Entry(path_frame)
download_path_entry.insert(0, config["download_path"])
download_path_entry.pack(side="left", fill="x", expand=True)
tk.Button(path_frame, text="Browse...", command=select_download_path).pack(side="left", padx=5)
tk.Button(path_frame, text="Open", command=open_download_path).pack(side="left", padx=5)

options_frame = tk.Frame(root)
options_frame.pack(fill="x", padx=10, pady=5, anchor="w")
embed_thumbnail_var = tk.BooleanVar(value=config["embed_thumbnail"])
tk.Checkbutton(options_frame, text="Embed Thumbnail", variable=embed_thumbnail_var).pack(side="left")
add_track_number_var = tk.BooleanVar(value=config.get("add_track_number", True))
tk.Checkbutton(options_frame, text="Add Track Num", variable=add_track_number_var).pack(side="left", padx=(10, 0))
tk.Button(options_frame, text="Save Settings", command=save_limit_settings).pack(side="right")

subtitles_frame = tk.Frame(root)
subtitles_frame.pack(fill="x", padx=10, pady=(0,5), anchor="w")
download_subtitles_var = tk.BooleanVar(value=config["download_subtitles_enabled"])
download_subtitles_check = tk.Checkbutton(subtitles_frame, text="Download Subtitles", variable=download_subtitles_var, state="disabled")
download_subtitles_check.pack(side="left")
subtitle_lang_combo = ttk.Combobox(subtitles_frame, values=[], width=10, state="disabled")
subtitle_lang_combo.set(config["subtitle_language"])
subtitle_lang_combo.pack(side="left", padx=5)
loading_label = tk.Label(subtitles_frame, text="", width=15)
loading_label.pack(side="left", padx=5)

preview_frame = tk.Frame(root)
preview_frame.pack(fill="both", expand=True, padx=10)
preview_control_frame = tk.Frame(preview_frame)
preview_control_frame.pack(fill="x")
tk.Label(preview_control_frame, text="Preview:").pack(side="left", pady=(5,0))
tk.Button(preview_control_frame, text="Refresh", command=refresh_history).pack(side="right", padx=(5, 0), pady=(5,0))
tk.Button(preview_control_frame, text="Clear", command=deselect_all).pack(side="right", padx=5, pady=(5,0))
tk.Button(preview_control_frame, text="Select All", command=select_all).pack(side="right", padx=5, pady=(5,0))
tk.Button(preview_control_frame, text="Select New", command=select_undownloaded).pack(side="right", padx=5, pady=(5,0))

columns = ("check", "url", "title", "duration", "last_download", "video_id", "content_type", "playlist_title", "channel_name", "subtitles", "playlist_index")
preview_tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=15)
preview_tree.heading("check", text="✓"); preview_tree.heading("url", text="URL"); preview_tree.heading("title", text="Title", command=lambda: sort_treeview("title")); preview_tree.heading("duration", text="Duration", command=lambda: sort_treeview("duration")); preview_tree.heading("last_download", text="Last DL", command=lambda: sort_treeview("last_download"))
preview_tree.column("check", width=30, anchor="center", stretch=False); preview_tree.column("url", width=150, stretch=False); preview_tree.column("title", width=350); preview_tree.column("duration", width=70, anchor="center", stretch=False); preview_tree.column("last_download", width=120, anchor="center", stretch=False)
for col in ["video_id", "content_type", "playlist_title", "channel_name", "subtitles", "playlist_index"]: preview_tree.column(col, width=0, stretch=tk.NO)
preview_tree.pack(fill="both", expand=True, pady=5)
preview_tree.bind("<Button-1>", toggle_check)
preview_tree.bind("<KeyRelease-space>", toggle_check_with_space)
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
tk.Label(log_frame, text="Log:").pack(anchor="w")
log_text = tk.Text(log_frame, height=8)
log_text.pack(fill="both", expand=True, pady=5)
log_text.config(state="normal")

update_format_combobox_visibility()

root.mainloop()