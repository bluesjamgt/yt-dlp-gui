# yt-dlp Downloader GUI v2.328 (Phase 3 - Native Checkbox, MenuBar I18N, Fixed Download)
import os
import sys
import json
import sqlite3
import re
import platform
import glob
import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSplitter, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QTreeWidget, QTreeWidgetItem, QProgressBar, QTextEdit, QFrame, QListWidget, 
    QFileDialog, QSpinBox, QDialog, QDialogButtonBox, QListWidgetItem, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QPixmap
import webbrowser

try:
    from yt_dlp import YoutubeDL
except ImportError:
    print("Error: Module 'yt-dlp' not found! Please run: pip install yt-dlp")
    sys.exit()

# ==========================================
# 📂 系統路徑與全域變數
# ==========================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "ytdlp_data")
DB_PATH = os.path.join(DATA_DIR, "history.db")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "thumbnails"), exist_ok=True)

AUDIO_QUALITY_MAP = {
    "320 kbps (Best)": "0", "256 kbps": "1", "192 kbps": "2", 
    "140 kbps": "3", "128 kbps": "4", "96 kbps": "5",
}
REVERSE_AUDIO_QUALITY_MAP = {v: k for k, v in AUDIO_QUALITY_MAP.items()}

I18N = {
    "en": {
        "url": "URL:", "analyze": "Analyze", "limit": "Limit (0=All):",
        "type": "Type:", "res": "Res:", "audio": "Audio:", "path": "Path:",
        "browse": "Browse...", "open": "Open", "embed_thumb": "Embed Thumbnail",
        "add_track": "Add Track Num", "dl_subtitles": "Download Subtitles", 
        "preview": "Preview:", "refresh": "Refresh", "clear": "Clear", 
        "select_all": "Select All", "select_new": "Select New", 
        "download": "Download", "cancel": "Cancel", "log": "Log:",
        "col_url": "URL", "col_title": "Title", "col_duration": "Duration", "col_lastdl": "Last DL",
        "menu_file": "File", "action_open_dl": "📂 Open DL Folder", "action_exit": "❌ Exit",
        "menu_settings": "Settings", "action_save_cfg": "💾 Save Config",
        "menu_lang": "Language", "action_tw": "繁體中文", "action_en": "English", "action_ja": "日本語",
        "menu_tools": "Tools", "action_import_json": "📥 Import JSON History", 
        "action_fetch_meta": "🔄 Fetch Missing Meta", "action_scan_all": "🔎 Scan File Locations",
        "lbl_control_title": "⚙️ Video Control Tower", "lbl_history_title": "🗃️ Media History DB",
        "ctx_folder": "📂 Show in Folder", "ctx_copy": "🔗 Copy Link Address", "ctx_browser": "🌐 Open in Browser",
        "ctx_fetch": "🔍 Fetch Missing Meta", "ctx_scan_silent": "🔍 Find Missing Files (Default)",
        "ctx_scan_custom": "📂 Select File Location...", "ctx_remove": "❌ Remove from List",
        "ctx_delete": "🗑️ Delete File", "ctx_clear": "🧹 Clear Entire List", 
        "ctx_dl": "⬇ Download Submenu",
        "ctx_dl_channel": "📺 Parse Entire Channel",
        "ctx_dl_video": "🎬 Download Video Directly",
        "ctx_dl_audio": "🎵 Download Audio Directly",
        "ctx_dl_cover": "🖼️ Download Thumbnail (Cover)",
        "tb_video": "🎬 Video", "tb_audio": "🎵 Audio", "tb_cover": "🖼️ Cover",
        "tb_remove": "❌ Remove", "tb_clear_dead": "🧹 Clear Dead", "ph_search": "🔍 Search Title, Channel, URL...",
        "action_dl_organize": "📁 Download Organization...",
        "dlg_organize_title": "Download Organization Settings",
        "dlg_by_channel": "Organize by Channel Name",
        "dlg_by_type": "Organize by Content Type (Videos / Shorts / Playlists)",
        "log_saved": "✅ Settings saved.",
        "log_refresh": "History refreshed.",
        "log_analyze_start": "Starting analysis...",
        "log_analyze_fail": "Analysis failed: Invalid URL or network error.",
        "log_analyze_no_video": "No videos found.",
        "log_analyze_ok_count": "Analysis complete. Found {} items.",
        "log_analyze_ok": "Analysis complete.",
        "log_dl_processing": "⬇ ({0}/{1}) Processing: {2}",
        "log_dl_saved": "Saved: {0}",
        "log_dl_warning": "Warning '{0}': {1}",
        "log_dl_done": "All tasks completed.",
        "log_dl_cancelled": "Cancelled by user"
    },
    "zh-TW": {
        "url": "影片網址:", "analyze": "分析", "limit": "解析限制 (0=全部):",
        "type": "格式類型:", "res": "最高畫質:", "audio": "音質:", "path": "儲存路徑:",
        "browse": "瀏覽...", "open": "開啟", "embed_thumb": "寫入封面圖",
        "add_track": "加入音軌序號", "dl_subtitles": "下載字幕", 
        "preview": "下載預覽清單:", "refresh": "重整紀錄", "clear": "清除選取", 
        "select_all": "全選", "select_new": "選取未下載", 
        "download": "開始下載", "cancel": "取消", "log": "執行紀錄:",
        "col_url": "網址", "col_title": "影片標題", "col_duration": "影片時長", "col_lastdl": "最後下載時間",
        "menu_file": "檔案 (File)", "action_open_dl": "📂 開啟下載目錄", "action_exit": "❌ 結束",
        "menu_settings": "設定 (Settings)", "action_save_cfg": "💾 儲存當前設定",
        "menu_lang": "語系 (Language)", "action_tw": "繁體中文 (zh-TW)", "action_en": "English (en)", "action_ja": "日本語 (ja-JP)",
        "menu_tools": "工具 (Tools)", "action_import_json": "📥 匯入舊版 JSON 歷史", 
        "action_fetch_meta": "🛜 取得資訊", "action_scan_all": "🔎 掃描檔案位置",
        "lbl_control_title": "⚙️ 影片下載控制塔", "lbl_history_title": "🗃️ 影音歷史資料庫",
        "ctx_folder": "📂 在資料夾中顯示", "ctx_copy": "🔗 複製連結位址", "ctx_browser": "🌐 在瀏覽器中打開連結",
        "ctx_fetch": "🛜 取得資訊", "ctx_scan_silent": "🔍 尋找遺失檔案",
        "ctx_scan_custom": "📂 選擇檔案位置...", "ctx_remove": "❌ 從列表中移除",
        "ctx_delete": "🗑️ 刪除檔案", "ctx_clear": "🧹 從列表中全部移除",
        "ctx_dl": "⬇ 下載檔案至..",
        "ctx_dl_channel": "📺 解析頻道所有影片",
        "ctx_dl_video": "🎬 下載影片 (Video)",
        "ctx_dl_audio": "🎵 下載音訊 (Audio)",
        "ctx_dl_cover": "🖼️ 下載縮圖 (Cover)",
        "tb_video": "🎬 影片", "tb_audio": "🎵 音訊", "tb_cover": "🖼️ 縮圖",
        "tb_remove": "❌ 刪除列表", "tb_clear_dead": "🧹 清除失效", "ph_search": "🔍 搜尋標題、頻道、網址...",
        "action_dl_organize": "⚙️ 下載設定 ..",
        "dlg_organize_title": "下載路徑分類設定",
        "dlg_by_channel": "依照頻道名稱分類",
        "dlg_by_type": "依照內容類型分類 (Videos / Shorts / Playlists)",
        "log_saved": "✅ 設定已儲存。",
        "log_refresh": "紀錄已重整。",
        "log_analyze_start": "開始分析...",
        "log_analyze_fail": "分析失敗: 無效的網址或網路錯誤。",
        "log_analyze_no_video": "找不到任何影片。",
        "log_analyze_ok_count": "分析完成。共找到 {} 個項目。",
        "log_analyze_ok": "分析完成。",
        "log_dl_processing": "⬇ ({0}/{1}) 處理中: {2}",
        "log_dl_saved": "儲存成功: {0}",
        "log_dl_warning": "處理警告 '{0}': {1}",
        "log_dl_done": "所有任務執行完畢。",
        "log_dl_cancelled": "手動取消下載"
    },
    "ja": {
        "url": "URL:", "analyze": "分析", "limit": "制限 (0=全て):",
        "type": "形式:", "res": "解像度:", "audio": "音声:", "path": "保存先:",
        "browse": "参照...", "open": "開く", "embed_thumb": "サムネイル追加",
        "add_track": "トラック番号追加", "dl_subtitles": "字幕をダウンロード", 
        "preview": "プレビュー:", "refresh": "更新", "clear": "クリア", 
        "select_all": "全て選択", "select_new": "未ダウンロード選択", 
        "download": "ダウンロード", "cancel": "キャンセル", "log": "ログ:",
        "col_url": "URL", "col_title": "タイトル", "col_duration": "長さ", "col_lastdl": "最終DL日時",
        "menu_file": "ファイル (File)", "action_open_dl": "📂 DLフォルダを開く", "action_exit": "❌ 終了",
        "menu_settings": "設定 (Settings)", "action_save_cfg": "💾 設定を保存",
        "menu_lang": "言語 (Language)", "action_tw": "繁體中文 (zh-TW)", "action_en": "English (en)", "action_ja": "日本語 (ja)",
        "menu_tools": "ツール (Tools)", "action_import_json": "📥 JSON履歴をインポート", 
        "action_fetch_meta": "🔄 情報を取得", "action_scan_all": "🔎 ファイルの場所をスキャン",
        "lbl_control_title": "⚙️ ダウンロード コントロールタワー", "lbl_history_title": "🗃️ 履歴データベース",
        "ctx_folder": "📂 フォルダに表示", "ctx_copy": "🔗 リンクアドレスをコピー", "ctx_browser": "🌐 ブラウザで開く",
        "ctx_fetch": "🔍 情報を取得", "ctx_scan_silent": "🔍 不足ファイルを検索",
        "ctx_scan_custom": "📂 ファイルの場所を選択...", "ctx_remove": "❌ リストから削除",
        "ctx_delete": "🗑️ ファイルを削除", "ctx_clear": "🧹 リストを全てクリア", 
        "ctx_dl": "⬇ ダウンロード先..",
        "ctx_dl_channel": "📺 チャンネルを一括ダウンロード",
        "ctx_dl_video": "🎬 動画をダウンロード (Video)",
        "ctx_dl_audio": "🎵 音声をダウンロード (Audio)",
        "ctx_dl_cover": "🖼️ サムネイルをダウンロード (Cover)",
        "tb_video": "🎬 動画", "tb_audio": "🎵 音声", "tb_cover": "🖼️ サムネイル",
        "tb_remove": "❌ 削除", "tb_clear_dead": "🧹 無効な履歴をクリア", "ph_search": "🔍 タイトル、チャンネル、URLを検索...",
        "action_dl_organize": "📁 ダウンロード整理設定...",
        "dlg_organize_title": "ダウンロード整理設定",
        "dlg_by_channel": "チャンネル名で整理する",
        "dlg_by_type": "コンテンツタイプで整理する (Videos / Shorts / Playlists)",
        "log_saved": "✅ 設定を保存しました。",
        "log_refresh": "履歴を更新しました。",
        "log_analyze_start": "分析を開始...",
        "log_analyze_fail": "分析失敗: 無効なURLまたはネットワークエラー。",
        "log_analyze_no_video": "動画が見つかりません。",
        "log_analyze_ok_count": "分析完了。{} 個のアイテムを見つけました。",
        "log_analyze_ok": "分析完了。",
        "log_dl_processing": "⬇ ({0}/{1}) 処理中: {2}",
        "log_dl_saved": "保存に成功: {0}",
        "log_dl_warning": "処理警告 '{0}': {1}",
        "log_dl_done": "すべてのタスクが完了しました。",
        "log_dl_cancelled": "手動でキャンセルしました"
    }
}

def sanitize_filename(filename): 
    return re.sub(r'[\\/:*?"<>|]', '_', filename).strip().rstrip('.')

class ThumbnailWorker(QThread):
    finished_signal = pyqtSignal(str, str)
    def __init__(self, video_id, url):
        super().__init__()
        self.video_id, self.url = video_id, url
    def run(self):
        try:
            ydl_opts = {"quiet": True, "skip_download": True, "extractor_args": {'youtube': ['player_client=default']}}
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if info and info.get("thumbnail"):
                    import requests
                    r = requests.get(info["thumbnail"], timeout=10)
                    if r.status_code == 200:
                        ext = "webp" if ".webp" in info["thumbnail"] else "jpg"
                        tp = os.path.join(DATA_DIR, "thumbnails", f"{self.video_id}.{ext}")
                        with open(tp, 'wb') as f: f.write(r.content)
                        self.finished_signal.emit(self.video_id, tp)
        except: pass

class MetadataWorker(QThread):
    progress_signal = pyqtSignal(str)
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks
    def run(self):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        self.progress_signal.emit(f"開始多執行緒補齊 {len(self.tasks)} 筆影片資訊...")
        ydl_opts = {"quiet": True, "skip_download": True, "extractor_args": {'youtube': ['player_client=web']}}
        import requests
        
        def fetch_task(idx, vid, url):
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info: raise Exception("No info returned")
                title = info.get("title", "Unknown")
                dur = info.get("duration"); dur_text = f"{int(dur)//60:02d}:{int(dur)%60:02d}" if dur else "Unknown"
                channel = info.get("uploader", "Unknown")
                th_url = info.get("thumbnail")
                tp = ""
                if th_url:
                    r = requests.get(th_url, timeout=10)
                    if r.status_code == 200:
                        ext = "webp" if ".webp" in th_url else "jpg"
                        tp = os.path.join(DATA_DIR, "thumbnails", f"{vid}.{ext}")
                        with open(tp, 'wb') as f: f.write(r.content)
                
                conn = sqlite3.connect(DB_PATH)
                conn.execute("UPDATE downloads SET title=?, duration=?, channel=?, thumbnail_path=? WHERE video_id=?", (title, dur_text, channel, tp, vid))
                conn.commit(); conn.close()
                self.update_signal.emit(vid)
                self.progress_signal.emit(f"({idx}/{len(self.tasks)}) 補齊完成: {title}")
                return vid
                
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(fetch_task, i+1, task[0], task[1]): task for i, task in enumerate(self.tasks)}
            for future in as_completed(futures):
                task = futures[future]
                try: future.result()
                except Exception as e:
                    self.progress_signal.emit(f"補齊失敗 {task[0]}: {e}")
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("UPDATE downloads SET title='Not Found (404)' WHERE video_id=? AND title IS NULL", (task[0],))
                    conn.commit(); conn.close()
                    self.update_signal.emit(task[0])
                    
        self.finished_signal.emit()

class HistoryCardWidget(QFrame):
    def __init__(self, record_dict, parent_window=None, parent=None):
        super().__init__(parent)
        self.setObjectName("historyCard")
        self.record = record_dict
        self.parent_window = parent_window
        self.setFixedHeight(78)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(120, 68)
        self.thumb_label.setScaledContents(True)
        self._load_thumbnail(record_dict.get('thumbnail_path', ''))
        
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(5, 0, 0, 0)
        t_str = record_dict.get('title') or 'Unknown'
        if len(t_str) > 55: t_str = t_str[:52] + '...'
        self.lbl_title = QLabel(t_str)
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #1F2937; background: transparent;")
        self.lbl_title.setWordWrap(False)
        
        meta_layout = QHBoxLayout()
        self.lbl_dur = QLabel(record_dict.get('duration') or '?')
        self.lbl_dur.setStyleSheet("color: #6B7280; font-size: 11px; background: transparent;")
        meta_layout.addWidget(self.lbl_dur)
        
        dot1 = QLabel("·"); dot1.setStyleSheet("color: #6B7280; font-size: 11px; background: transparent;")
        meta_layout.addWidget(dot1)
        
        self.lbl_size = QLabel()
        self.lbl_size.setStyleSheet("color: #6B7280; font-size: 11px; background: transparent;")
        meta_layout.addWidget(self.lbl_size)
        
        dot2 = QLabel("·"); dot2.setStyleSheet("color: #6B7280; font-size: 11px; background: transparent;")
        meta_layout.addWidget(dot2)
        
        fps = [fp for fp in (record_dict.get('filepath') or '').split('|') if fp]
        def ext_priority(fp):
            e = fp.split('.')[-1].lower()
            if e in ['mp4', 'mkv', 'webm', 'm4v']: return 1
            if e in ['mp3', 'm4a', 'flac', 'opus', 'wav']: return 2
            return 3
        fps.sort(key=ext_priority)
        
        self.combo_ext = None
        self.lbl_ext = None
        self.current_fp = None
        
        if len(fps) > 1:
            self.combo_ext = QComboBox()
            self.combo_ext.setStyleSheet("QComboBox { padding: 0px 0px; border: none; font-size: 11px; font-weight: bold; color: #6B7280; background: transparent; } QComboBox::drop-down { border: none; }")
            for f in fps:
                self.combo_ext.addItem(f.split('.')[-1].lower() + ' ▼', f)
            self.combo_ext.currentIndexChanged.connect(self._update_size_label)
            meta_layout.addWidget(self.combo_ext)
            self.current_fp = fps[0]
        else:
            ext_text = fps[0].split('.')[-1].lower() if fps else (record_dict.get('format') or 'Unknown').split('|')[0]
            self.lbl_ext = QLabel(ext_text)
            self.lbl_ext.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: bold; background: transparent;")
            meta_layout.addWidget(self.lbl_ext)
            if fps: self.current_fp = fps[0]
            
        dot3 = QLabel("·"); dot3.setStyleSheet("color: #6B7280; font-size: 11px; background: transparent;")
        meta_layout.addWidget(dot3)
        self.lbl_channel = QLabel(record_dict.get('channel') or '?')
        self.lbl_channel.setStyleSheet("color: #6B7280; font-size: 11px; background: transparent;")
        meta_layout.addWidget(self.lbl_channel)
        meta_layout.addStretch()
        
        info_layout.addWidget(self.lbl_title)
        info_layout.addLayout(meta_layout)
        
        layout.addWidget(self.thumb_label)
        layout.addLayout(info_layout)
        
        self.setStyleSheet("#historyCard { background-color: transparent; }")
        self._update_size_label()

    def _update_size_label(self):
        if self.combo_ext: self.current_fp = self.combo_ext.currentData()
        if self.current_fp and os.path.exists(self.current_fp):
            size_bytes = os.path.getsize(self.current_fp)
            filesize = f"{size_bytes/(1024*1024*1024):.1f} GB" if size_bytes >= 1024**3 else f"{size_bytes/(1024*1024):.1f} MB" if size_bytes >= 1024**2 else f"{size_bytes/1024:.1f} KB"
            self.lbl_size.setText(filesize)
        else:
            self.lbl_size.setText("Missing" if self.current_fp else "N/A")

    def _has_playable_file(self):
        """Check if any existing file is a playable video/audio (not just an image)."""
        fp_str = self.record.get('filepath') or ''
        for f in fp_str.split('|'):
            if f and os.path.exists(f):
                ext = f.split('.')[-1].lower()
                if ext in ('mp4', 'mkv', 'webm', 'm4v', 'mp3', 'm4a', 'flac', 'opus', 'wav'):
                    return True
        return False

    def _load_thumbnail(self, th_path):
        fp_str = self.record.get('filepath') or ''
        fps = [f for f in fp_str.split('|') if f and os.path.exists(f)]
        has_file = len(fps) > 0
        has_playable = self._has_playable_file()
        
        if th_path and os.path.exists(th_path):
            pm_raw = QPixmap(th_path)
            if pm_raw.isNull():
                self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if has_playable:
                    self.thumb_label.setText("▶")
                    self.thumb_label.setStyleSheet("background-color: #E5E7EB; color: #374151; font-weight: bold; font-size: 22px; border-radius: 4px;")
                else:
                    self.thumb_label.setText("⚠")
                    self.thumb_label.setStyleSheet("background-color: #FEE2E2; color: #991B1B; font-size: 16px; border-radius: 4px;")
                return

            pm = pm_raw.copy()
            if has_playable:
                from PyQt6.QtGui import QPainter, QColor, QBrush, QPolygonF
                from PyQt6.QtCore import QPointF
                painter = QPainter()
                painter.begin(pm)
                try:
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    center = QPointF(pm.rect().center())
                    radius = min(pm.width(), pm.height()) * 0.2
                    painter.setBrush(QBrush(QColor(0, 0, 0, 160)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(center, radius, radius)
                    
                    painter.setBrush(QBrush(QColor(255, 255, 255)))
                    poly = QPolygonF([
                        QPointF(center.x() - radius*0.3, center.y() - radius*0.4),
                        QPointF(center.x() + radius*0.5, center.y()),
                        QPointF(center.x() - radius*0.3, center.y() + radius*0.4)
                    ])
                    painter.drawPolygon(poly)
                finally:
                    painter.end()
            self.thumb_label.setPixmap(pm)
            self.thumb_label.setStyleSheet("")
        else:
            self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if has_playable:
                self.thumb_label.setText("▶")
                self.thumb_label.setStyleSheet("background-color: #E5E7EB; color: #374151; font-weight: bold; font-size: 22px; border-radius: 4px;")
            elif has_file:
                self.thumb_label.setText("🖼")
                self.thumb_label.setStyleSheet("background-color: #E5E7EB; color: #6B7280; font-size: 22px; border-radius: 4px;")
            else:
                self.thumb_label.setText("")
                self.thumb_label.setStyleSheet("background-color: #F3F4F6; border-radius: 4px;")

    def update_thumbnail(self, vid, new_path):
        if self.record.get('video_id') == vid and os.path.exists(new_path):
            self.record['thumbnail_path'] = new_path
            self.thumb_label.setText("")
            self._load_thumbnail(new_path)
            conn = sqlite3.connect(DB_PATH)
            conn.execute("UPDATE downloads SET thumbnail_path=? WHERE video_id=?", (new_path, vid))
            conn.commit(); conn.close()

    def open_folder(self):
        fp = self.record.get('filepath') or ''
        folder = os.path.dirname(fp) if fp else ''
        if not folder or not os.path.exists(folder):
            bp = self.parent_window.path_input.text() if getattr(self, 'parent_window', None) else ''
            ch = self.record.get('channel') or ''
            folder = os.path.join(bp, ch) if ch and bp else bp
            if not folder or not os.path.exists(folder):
                folder = bp if os.path.exists(bp) else ''
        if folder and os.path.exists(folder):
            if platform.system() == "Windows": os.startfile(folder)
            elif platform.system() == "Darwin": os.system(f"open '{folder}'")

# ==========================================
# ⚙️ 背景執行緒：解析與下載
# ==========================================
class ParseWorker(QThread):
    log_signal = pyqtSignal(str)
    item_signal = pyqtSignal(int, dict, str, str, str)
    finished_signal = pyqtSignal()
    
    def __init__(self, url, limit, i18n_dict=None):
        super().__init__()
        self.url, self.limit = url, limit
        self.i18n = i18n_dict or I18N["zh-TW"]

    def run(self):
        try:
            self.log_signal.emit(self.i18n.get("log_analyze_start", "開始分析..."))
            ydl_opts = {"quiet": True, "ignoreerrors": True, "extractor_args": {'youtube': ['player_client=default']}}
            if self.limit > 0: ydl_opts["playlistend"] = self.limit
            if "youtube.com/@" in self.url and any(x in self.url for x in ["/videos", "/shorts", "/streams"]):
                ydl_opts["extract_flat"] = True

            with YoutubeDL(ydl_opts) as ydl: info = ydl.extract_info(self.url, download=False)
            if not info: return self.log_signal.emit(self.i18n.get("log_analyze_fail", "分析失敗: 無效的網址或網路錯誤。"))

            if "entries" in info:
                entries = [e for e in info.get("entries", []) if e]
                if not entries: return self.log_signal.emit(self.i18n.get("log_analyze_no_video", "找不到任何影片。"))
                playlist_title = sanitize_filename(info.get("title", "Unknown Playlist"))
                channel_name = sanitize_filename(info.get("uploader", "Unknown Channel"))
                for idx, entry in enumerate(entries, start=1):
                    entry['playlist_index'] = entry.get('playlist_index') or idx
                    self.item_signal.emit(idx, entry, "playlist_video", playlist_title, channel_name)
                self.log_signal.emit(self.i18n.get("log_analyze_ok_count", "分析完成。共找到 {} 個項目。").replace("{}", str(len(entries))))
            else:
                channel_name = sanitize_filename(info.get("uploader", "Unknown Channel"))
                self.item_signal.emit(1, info, "video", "", channel_name)
                self.log_signal.emit(self.i18n.get("log_analyze_ok", "分析完成。"))
        except Exception as e: self.log_signal.emit(f"錯誤: {e}")
        finally: self.finished_signal.emit()

class DownloadWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()

    def __init__(self, settings, items, exact_path=False, i18n_dict=None):
        super().__init__()
        self.settings = settings
        self.items = items
        self.exact_path = exact_path
        self._is_cancelled = False
        self.i18n = i18n_dict or I18N["zh-TW"]

    def cancel(self): self._is_cancelled = True

    def run(self):
        dl_type = self.settings['type']
        target_ext = self.settings['v_format'] if dl_type == "Video" else self.settings['a_format']
        if dl_type == "Subtitle": target_ext = "srt"
        elif dl_type == "Cover": target_ext = "webp"

        ffmpeg_exe = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
        ffmpeg_exe_path = os.path.join(BASE_DIR, ffmpeg_exe)
        ydl_opts_base = {'ffmpeg_location': BASE_DIR} if os.path.exists(ffmpeg_exe_path) else {}
        
        total = len(self.items)

        for idx, item in enumerate(self.items, start=1):
            if self._is_cancelled: break
            
            url, title, video_id, content_type, playlist_title, channel_name, playlist_index, sub_langs, duration = item[:9]
            override_path = item[9] if len(item) > 9 else None
            
            if self.exact_path and override_path:
                final_dl_path = os.path.normpath(override_path)
            elif self.exact_path:
                final_dl_path = os.path.normpath(self.settings['path'])
            else:
                parts = [self.settings['path']]
                by_channel = self.settings.get('organize_by_channel', True)
                by_type = self.settings.get('organize_by_type', True)
                
                if by_channel:
                    parts.append(channel_name)
                if by_type:
                    if content_type == "playlist_video":
                        parts.append("Playlists")
                        parts.append(playlist_title)
                    elif content_type == "short":
                        parts.append("Shorts")
                    else:
                        parts.append("Videos")
                
                final_dl_path = os.path.normpath(os.path.join(*parts))
            os.makedirs(final_dl_path, exist_ok=True)

            final_title = f"{int(playlist_index):02d} - {title}" if self.settings['add_track'] and playlist_index else title
            base_outtmpl = os.path.join(final_dl_path, sanitize_filename(final_title))
            sandbox_outtmpl = f"{base_outtmpl}_ytdlptmp"

            self.log_signal.emit(self.i18n.get("log_dl_processing", "⬇ ({0}/{1}) 處理中: {2}").format(idx, total, final_title))

            ydl_opts = dict(ydl_opts_base)
            ydl_opts.update({
                "quiet": True, "noplaylist": True, "outtmpl": f"{sandbox_outtmpl}.%(ext)s",
                "extractor_args": {'youtube': ['player_client=ios,android,web']}
            })
            
            pps = []
            if dl_type == "Video":
                h_limit = self.settings['res'].replace("p", "")
                ydl_opts.update({"format": f"bestvideo[height<={h_limit}]+bestaudio/best", "merge_output_format": target_ext})
            elif dl_type == "Audio":
                bitrate = re.search(r'(\d+)', self.settings['a_res']).group(1) if re.search(r'(\d+)', self.settings['a_res']) else "192"
                ydl_opts.update({"format": "bestaudio/best"})
                pps.append({'key': 'FFmpegExtractAudio', 'preferredcodec': target_ext, 'preferredquality': bitrate})
            elif dl_type == "Cover":
                ydl_opts.update({"writethumbnail": True, "skip_download": True})
                pps.append({'key': 'FFmpegThumbnailsConvertor', 'format': target_ext})
            elif dl_type == "Subtitle":
                ydl_opts.update({"skip_download": True})

            should_dl_sub = (dl_type == "Subtitle") or self.settings['dl_sub']
            if should_dl_sub:
                ydl_opts.update({"writesubtitles": True, "writeautomaticsub": False, "subtitlesformat": "srt"})
                pps.append({'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'})
                selected_lang = self.settings['sub_lang']
                ydl_opts['subtitleslangs'] = [selected_lang] if selected_lang and selected_lang != "all" else ['all', '-live_chat']

            if dl_type not in ["Cover", "Subtitle"]:
                ydl_opts["writethumbnail"] = True
            if self.settings['embed_thumb'] and dl_type not in ["Cover", "Subtitle"]:
                pps.extend([{'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'}, {'key': 'FFmpegMetadata'}, {'key': 'EmbedThumbnail'}])

            if pps: ydl_opts["postprocessors"] = pps

            def hook(d):
                if self._is_cancelled:
                    raise Exception(self.i18n.get("log_dl_cancelled", "手動取消下載 / Cancelled by user"))
                if d["status"] == "downloading":
                    try:
                        # 💡 強制清洗 YT 傳回的雜訊字元，確保轉型為 int 不會崩潰
                        pct_str = d.get("_percent_str", "0%").strip().replace("%", "")
                        pct_str = re.sub(r'\x1b[^m]*m', '', pct_str) # 移除 ANSI 色彩碼
                        if pct_str != 'N/A' and pct_str != '~':
                            self.progress_signal.emit(int(float(pct_str)))
                    except Exception: pass
                elif d["status"] == "finished": 
                    self.progress_signal.emit(100)

            ydl_opts['progress_hooks'] = [hook]

            try:
                with YoutubeDL(ydl_opts) as ydl: ydl.download([url])
                
                import shutil
                thumb_path = ""
                # Step 1: Try to grab thumbnail from sandbox (before EmbedThumbnail ate it)
                for ext in ["jpg", "webp", "png"]:
                    sandbox_thumb = f"{sandbox_outtmpl}.{ext}"
                    if os.path.exists(sandbox_thumb):
                        target = os.path.join(DATA_DIR, "thumbnails", f"{video_id}.{ext}")
                        try:
                            shutil.copy2(sandbox_thumb, target)
                            thumb_path = target
                        except:
                            thumb_path = sandbox_thumb
                        break
                # Step 2: If EmbedThumbnail already ate it, check thumbnails cache
                if not thumb_path:
                    for ext in ["jpg", "webp", "png"]:
                        cached = os.path.join(DATA_DIR, "thumbnails", f"{video_id}.{ext}")
                        if os.path.exists(cached):
                            thumb_path = cached
                            break
                # Step 3: If still no thumbnail, fetch from YouTube API
                if not thumb_path:
                    try:
                        import requests
                        ydl_info_opts = {"quiet": True, "skip_download": True}
                        with YoutubeDL(ydl_info_opts) as ydl_info:
                            info_for_thumb = ydl_info.extract_info(url, download=False)
                            if info_for_thumb and info_for_thumb.get("thumbnail"):
                                r = requests.get(info_for_thumb["thumbnail"], timeout=10)
                                if r.status_code == 200:
                                    t_ext = "webp" if ".webp" in info_for_thumb["thumbnail"] else "jpg"
                                    tp = os.path.join(DATA_DIR, "thumbnails", f"{video_id}.{t_ext}")
                                    with open(tp, 'wb') as tf: tf.write(r.content)
                                    thumb_path = tp
                    except: pass
                
                for tmp_file in glob.glob(f"{sandbox_outtmpl}*"):
                    final_file = tmp_file.replace(sandbox_outtmpl, base_outtmpl)
                    if os.path.exists(final_file): os.remove(final_file)
                    os.rename(tmp_file, final_file)
                self.log_signal.emit(self.i18n.get("log_dl_saved", "儲存成功: {0}").format(final_title))
                
                conn = sqlite3.connect(DB_PATH)
                filesize = "Unknown"
                if os.path.exists(final_file):
                    size_bytes = os.path.getsize(final_file)
                    if size_bytes >= 1024*1024*1024: filesize = f"{size_bytes/(1024*1024*1024):.1f} GB"
                    elif size_bytes >= 1024*1024: filesize = f"{size_bytes/(1024*1024):.1f} MB"
                    else: filesize = f"{size_bytes/1024:.1f} KB"
                        
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT filepath, format, filesize, thumbnail_path FROM downloads WHERE video_id=?", (video_id,))
                existing = cur.fetchone()
                
                final_fp = final_file
                final_fmt = target_ext
                final_fs = filesize
                
                if not thumb_path and existing and existing['thumbnail_path']:
                    thumb_path = existing['thumbnail_path']
                
                if existing and existing['filepath']:
                    old_fps = [fp for fp in existing['filepath'].split('|') if fp]
                    old_fmts = [f for f in existing['format'].split('|') if f] if existing['format'] else []
                    old_fss = [s for s in (existing['filesize'] or '').split('|') if s]
                    
                    if final_file not in old_fps:
                        old_fps.append(final_file)
                        old_fmts.append(target_ext)
                        old_fss.append(filesize)
                        
                        final_fp = '|'.join(old_fps)
                        final_fmt = '|'.join(old_fmts)
                        final_fs = '|'.join(old_fss)
                    else:
                        idx = old_fps.index(final_file)
                        if idx < len(old_fss): old_fss[idx] = filesize
                        else: old_fss.append(filesize)
                        final_fp = '|'.join(old_fps)
                        final_fmt = '|'.join(old_fmts)
                        final_fs = '|'.join(old_fss)
                        
                dl_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                preserve_sort = None
                if existing:
                    # Preserve original download_time and sort_order for existing records
                    cur2 = conn.execute("SELECT download_time, sort_order FROM downloads WHERE video_id=?", (video_id,))
                    row2 = cur2.fetchone()
                    if row2 and row2['download_time']: dl_time = row2['download_time']
                    if row2 and row2['sort_order'] is not None: preserve_sort = row2['sort_order']
                else:
                    # New item: assign sort_order so it appears at the TOP of the list
                    cur_min = conn.execute("SELECT MIN(sort_order) FROM downloads").fetchone()
                    min_order = cur_min[0] if cur_min and cur_min[0] is not None else 0
                    preserve_sort = min_order - 1
                
                conn.execute('''INSERT OR REPLACE INTO downloads 
                                (video_id, url, title, format, channel, filepath, download_time, duration, filesize, thumbnail_path, sort_order) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                             (video_id, url, title, final_fmt, channel_name, final_fp, dl_time, duration, final_fs, thumb_path, preserve_sort))
                conn.commit(); conn.close()
                
            except Exception as e:
                self.log_signal.emit(self.i18n.get("log_dl_warning", "處理警告 '{0}': {1}").format(final_title, e))
                for tmp_file in glob.glob(f"{sandbox_outtmpl}*"):
                    try: os.remove(tmp_file)
                    except: pass

        self.log_signal.emit(self.i18n.get("log_dl_done", "所有任務執行完畢。"))
        self.finished_signal.emit()

# ==========================================
# 🎨 UI 主視窗
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("yt-dlp Downloader v2.0 (Phase 3)")
        self.resize(1200, 800)
        
        self.loaded_config = self._load_old_config()
        self.current_lang = self.loaded_config.get("language", "zh-TW")
        
        self._init_db()
        self._setup_menubar()
        self._setup_ui()
        self._apply_styles()
        self._restore_settings_to_ui()
        self.update_ui_language()
        self.load_history_list()

    def _load_old_config(self):
        default_config = {
            "download_path": os.path.expanduser('~/Downloads'), 
            "video_limit": "1080p", "audio_quality": "320 kbps (Best)", 
            "video_format": "mp4", "audio_format": "mp3", 
            "embed_thumbnail": True, "add_track_number": True, 
            "download_subtitles_enabled": False, "subtitle_language": "zh-TW",
            "playlist_limit": 0, "url_history": [], "language": "zh-TW",
            "organize_by_channel": True, "organize_by_type": True
        }
        paths = [os.path.join(BASE_DIR, "config.json"), os.path.expanduser("~/.ytdlpgui_config.json"), CONFIG_FILE]
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f: default_config.update(json.load(f))
                except: pass
        return default_config

    def _save_config(self):
        try:
            cfg = self.loaded_config
            cfg["download_path"] = self.path_input.text()
            cfg["video_limit"] = self.res_combo.currentText()
            cfg["audio_quality"] = self.audio_res_combo.currentText()
            cfg["video_format"] = self.vformat_combo.currentText()
            cfg["audio_format"] = self.aformat_combo.currentText()
            cfg["embed_thumbnail"] = self.chk_embed.isChecked()
            cfg["add_track_number"] = self.chk_track.isChecked()
            cfg["download_subtitles_enabled"] = self.chk_sub.isChecked()
            cfg["subtitle_language"] = self.sub_combo.currentText()
            cfg["playlist_limit"] = self.limit_spin.value()
            cfg["language"] = self.current_lang
            cfg["organize_by_channel"] = self.loaded_config.get("organize_by_channel", True)
            cfg["organize_by_type"] = self.loaded_config.get("organize_by_type", True)
            
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=4, ensure_ascii=False)
            lang_dict = I18N.get(self.current_lang, I18N["zh-TW"])
            self.log_msg(lang_dict.get("log_saved", "✅ 設定已儲存。"))
        except Exception as e: self.log_msg(f"儲存設定檔失敗: {e}")

    def _show_organize_dialog(self):
        lang = I18N.get(self.current_lang, I18N["zh-TW"])
        dlg = QDialog(self)
        dlg.setWindowTitle(lang.get("dlg_organize_title", "Download Organization"))
        dlg.setFixedWidth(420)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        lbl = QLabel(lang.get("dlg_organize_title", ""))
        lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl)
        
        chk_channel = QCheckBox(lang.get("dlg_by_channel", ""))
        chk_channel.setChecked(self.loaded_config.get("organize_by_channel", True))
        layout.addWidget(chk_channel)
        
        chk_type = QCheckBox(lang.get("dlg_by_type", ""))
        chk_type.setChecked(self.loaded_config.get("organize_by_type", True))
        layout.addWidget(chk_type)
        
        preview_label = QLabel()
        preview_label.setStyleSheet("color: #6B7280; font-size: 11px; padding: 8px; background: #F3F4F6; border-radius: 4px;")
        preview_label.setWordWrap(True)
        layout.addWidget(preview_label)
        
        def update_preview():
            base = self.path_input.text() or "D:\\Downloads"
            parts = [base]
            if chk_channel.isChecked(): parts.append("Channel")
            if chk_type.isChecked(): parts.append("Videos")
            example = os.path.join(*parts, "video.mp4")
            preview_label.setText(f"範例: {example}")
        
        chk_channel.stateChanged.connect(lambda: update_preview())
        chk_type.stateChanged.connect(lambda: update_preview())
        update_preview()
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)
        
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.loaded_config["organize_by_channel"] = chk_channel.isChecked()
            self.loaded_config["organize_by_type"] = chk_type.isChecked()
            self._save_config()
            self.log_msg(f"✅ 下載分類設定已更新。頻道={'ON' if chk_channel.isChecked() else 'OFF'}, 類型={'ON' if chk_type.isChecked() else 'OFF'}")

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.execute('''CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT, video_id TEXT UNIQUE, url TEXT,
            title TEXT, duration TEXT, filesize TEXT, format TEXT, channel TEXT,
            filepath TEXT, thumbnail_path TEXT, download_time DATETIME, sort_order INTEGER)''')
        try: conn.execute("ALTER TABLE downloads ADD COLUMN sort_order INTEGER")
        except: pass
        conn.commit(); conn.close()

    def _setup_menubar(self):
        menubar = self.menuBar()
        
        self.file_menu = menubar.addMenu("檔案")
        self.open_folder_action = QAction("📂 開啟下載資料夾", self)
        self.open_folder_action.triggered.connect(lambda: self._open_dir(self.path_input.text()))
        self.exit_action = QAction("❌ 結束", self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.open_folder_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.exit_action)

        self.settings_menu = menubar.addMenu("設定")
        self.save_settings_action = QAction("💾 儲存當前設定", self)
        self.save_settings_action.triggered.connect(self._save_config)
        self.settings_menu.addAction(self.save_settings_action)
        
        self.dl_organize_action = QAction("📁 下載分類設定...", self)
        self.dl_organize_action.triggered.connect(self._show_organize_dialog)
        self.settings_menu.addAction(self.dl_organize_action)

        self.lang_menu = menubar.addMenu("語系")
        self.action_tw = QAction("繁體中文", self)
        self.action_en = QAction("English", self)
        self.action_ja = QAction("日本語", self)
        self.action_tw.triggered.connect(lambda: self._change_lang("zh-TW"))
        self.action_en.triggered.connect(lambda: self._change_lang("en"))
        self.action_ja.triggered.connect(lambda: self._change_lang("ja"))
        self.lang_menu.addAction(self.action_tw); self.lang_menu.addAction(self.action_en); self.lang_menu.addAction(self.action_ja)

        self.tools_menu = menubar.addMenu("工具")
        self.import_json_action = QAction("📥 匯入舊版 JSON 歷史", self)
        self.import_json_action.triggered.connect(self.import_old_json)
        self.fetch_meta_action = QAction("🔄 連線擷取檔案資訊", self)
        self.fetch_meta_action.triggered.connect(self.fetch_missing_meta)
        self.scan_all_action = QAction("🔎 掃描檔案位置", self)
        self.scan_all_action.triggered.connect(lambda: self.run_local_scan(None, False))
        self.tools_menu.addAction(self.import_json_action); self.tools_menu.addAction(self.fetch_meta_action)
        self.tools_menu.addAction(self.scan_all_action)

    def import_old_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "匯入舊版 JSON 歷史", BASE_DIR, "JSON Files (*.json)")
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f: data = json.load(f)
            if not isinstance(data, dict): return self.log_msg("JSON 格式不符。")
            conn = sqlite3.connect(DB_PATH)
            success = 0
            for vid, dtime in data.items():
                url = f"https://www.youtube.com/watch?v={vid}"
                try:
                    conn.execute("INSERT OR IGNORE INTO downloads (video_id, url, download_time) VALUES (?, ?, ?)", (vid, url, dtime))
                    if conn.total_changes > 0: success += 1
                except: pass
            conn.commit(); conn.close()
            self.log_msg(f"✅ 成功匯入 {success} 筆歷史紀錄。")
            self.load_history_list()
        except Exception as e: self.log_msg(f"匯入失敗: {e}")

    def fetch_missing_meta(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT video_id, url FROM downloads WHERE title IS NULL AND url IS NOT NULL")
        tasks = cursor.fetchall()
        conn.close()
        
        if not tasks: return self.log_msg("🎉 所有歷史紀錄資訊皆已完整，無需考古。")
        self.meta_worker = MetadataWorker(tasks)
        self.meta_worker.progress_signal.connect(self.log_msg)
        self.meta_worker.update_signal.connect(self.load_history_list)
        self.meta_worker.finished_signal.connect(lambda: self.log_msg("✅ 手動補齊資訊作業完成。"))
        self.meta_worker.start()

    def _update_single_card(self, vid):
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            w = self.history_list.itemWidget(item)
            if w and w.record.get('video_id') == vid:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM downloads WHERE video_id=?", (vid,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    w.record.update(dict(row))
                    t_str = w.record.get('title') or 'Unknown'
                    if len(t_str) > 55: t_str = t_str[:52] + '...'
                    w.lbl_title.setText(t_str)
                    if hasattr(w, 'lbl_dur'): w.lbl_dur.setText(w.record.get('duration') or '?')
                    if hasattr(w, 'lbl_channel'): w.lbl_channel.setText(w.record.get('channel') or '?')
                    w._update_size_label()
                    w.thumb_label.setText("")
                    w._load_thumbnail(w.record.get('thumbnail_path', ''))
                break

    def run_local_scan(self, selected_items=None, silent=False):
        base_dir = self.path_input.text() if self.path_input.text() else BASE_DIR
        
        if silent: path = base_dir
        else:
            path = QFileDialog.getExistingDirectory(self, "選擇要掃描的根目錄", base_dir)
            if not path: return
            
        target_vids = []
        if selected_items:
            for sel_item in selected_items:
                w = self.history_list.itemWidget(sel_item)
                if w and w.record.get('video_id'): target_vids.append(w.record.get('video_id'))
                
        conn = sqlite3.connect(DB_PATH)
        fetch_tasks = []
        final_vids = []
        
        if target_vids:
            # We break into chunks of 900 to circumvent SQLite limitations
            for i in range(0, len(target_vids), 900):
                chunk = target_vids[i:i+900]
                query = f"SELECT video_id, url, title FROM downloads WHERE video_id IN ({','.join(['?']*len(chunk))})"
                cursor = conn.execute(query, chunk)
                for row in cursor.fetchall():
                    vid, url, title = row[0], row[1], row[2]
                    final_vids.append(vid)
                    if not title or title.strip() == '' or title == 'Unknown' or title == 'Not Found (404)':
                        if url: fetch_tasks.append((vid, url))
        else:
            cursor = conn.execute("SELECT video_id, url, title FROM downloads WHERE filepath IS NULL OR filepath = ''")
            for row in cursor.fetchall():
                vid, url, title = row[0], row[1], row[2]
                final_vids.append(vid)
                if not title or title.strip() == '' or title == 'Unknown' or title == 'Not Found (404)':
                    if url: fetch_tasks.append((vid, url))
        conn.close()
        
        if fetch_tasks:
            self.log_msg(f"🔎 發現 {len(fetch_tasks)} 筆目標缺乏影片標題資訊，正在背景自動補齊中...")
            worker = MetadataWorker(fetch_tasks)
            worker.update_signal.connect(self._update_single_card)
            worker.progress_signal.connect(self.log_msg)
            if not hasattr(self, 'meta_workers'): self.meta_workers = []
            self.meta_workers.append(worker)
            worker.finished_signal.connect(lambda w=worker: self.meta_workers.remove(w) if w in self.meta_workers else None)
            worker.finished_signal.connect(lambda: self._execute_scan(final_vids, path))
            worker.start()
        else:
            self._execute_scan(final_vids, path)

    def _execute_scan(self, target_vids, path):
        self.log_msg(f"🔎 開始掃描以匹配遺失的影片檔案...")
        conn = sqlite3.connect(DB_PATH)
        success = 0
        import re
        
        targets = []
        if target_vids:
            for i in range(0, len(target_vids), 900):
                chunk = target_vids[i:i+900]
                query = f"SELECT video_id, title, channel FROM downloads WHERE video_id IN ({','.join(['?']*len(chunk))})"
                cursor = conn.execute(query, chunk)
                for row in cursor.fetchall():
                    vid, title, channel = row[0], row[1] or '', row[2] or ''
                    if title == 'Not Found (404)': continue
                    title_clean = re.sub(r'[\\/:*?"<>|_\-\s\[\]\(\)]', '', title).strip().lower()
                    targets.append({'vid': vid, 'title': title_clean, 'channel': channel})
        else:
            cursor = conn.execute("SELECT video_id, title, channel FROM downloads WHERE filepath IS NULL OR filepath = ''")
            for row in cursor.fetchall():
                vid, title, channel = row[0], row[1] or '', row[2] or ''
                if title == 'Not Found (404)': continue
                title_clean = re.sub(r'[\\/:*?"<>|_\-\s\[\]\(\)]', '', title).strip().lower()
                targets.append({'vid': vid, 'title': title_clean, 'channel': channel})
                
        if not targets:
            self.log_msg("✅ 無需掃描，目標檔案皆已標明實體路徑或確認(404)失效。")
            conn.close()
            return
            
        matched = {t['vid']: [] for t in targets}
        
        def scan_dir(scan_path):
            for root, dirs, files in os.walk(scan_path):
                if not getattr(self, 'is_scanning', True): break
                for file in files:
                    lower_file = file.lower()
                    if not lower_file.endswith(('.mp4', '.mkv', '.webm', '.m4a', '.mp3', '.m4v', '.opus', '.flac', '.wav', '.srt', '.vtt')): continue
                    file_clean = re.sub(r'[\\/:*?"<>|_\-\s\[\]\(\)]', '', lower_file)
                    for t in targets:
                        if t['vid'] in matched and matched[t['vid']]: continue
                        if (t['title'] and len(t['title']) > 3 and t['title'] in file_clean) or (t['vid'] in file):
                            matched[t['vid']].append(os.path.normpath(os.path.join(root, file)))
        
        # Step 1: 先掃描頻道名稱目錄 (精準快速)
        channel_names = set(sanitize_filename(t['channel']) for t in targets if t['channel'] and t['channel'] != 'Unknown')
        scanned_channel_dirs = set()
        for ch_name in channel_names:
            ch_dir = os.path.join(path, ch_name)
            if os.path.isdir(ch_dir):
                self.log_msg(f"📂 Step 1: 掃描頻道目錄 {ch_name}/")
                scan_dir(ch_dir)
                scanned_channel_dirs.add(os.path.normpath(ch_dir))
        
        # 檢查是否還有未匹配的目標
        unmatched = [t for t in targets if not matched.get(t['vid'])]
        
        # Step 2: 還有未匹配的 → 全局掃描下載根目錄 (跳過已掃過的頻道目錄)
        if unmatched:
            self.log_msg(f"📂 Step 2: {len(unmatched)} 筆未命中，擴大掃描下載根目錄...")
            for root, dirs, files in os.walk(path):
                if not getattr(self, 'is_scanning', True): break
                norm_root = os.path.normpath(root)
                if any(norm_root.startswith(cd) for cd in scanned_channel_dirs): continue
                for file in files:
                    lower_file = file.lower()
                    if not lower_file.endswith(('.mp4', '.mkv', '.webm', '.m4a', '.mp3', '.m4v', '.opus', '.flac', '.wav', '.srt', '.vtt')): continue
                    file_clean = re.sub(r'[\\/:*?"<>|_\-\s\[\]\(\)]', '', lower_file)
                    for t in unmatched:
                        if t['vid'] in matched and matched[t['vid']]: continue
                        if (t['title'] and len(t['title']) > 3 and t['title'] in file_clean) or (t['vid'] in file):
                            matched[t['vid']].append(os.path.normpath(os.path.join(root, file)))

        for vid, fps in matched.items():
            if fps:
                fps = list(set(fps))
                joined_fp = '|'.join(fps)
                conn.execute("UPDATE downloads SET filepath=? WHERE video_id=?", (joined_fp, vid))
                success += 1

        conn.commit(); conn.close()
        self.log_msg(f"✅ 掃描與重構引擎結束，共重組 {success} 個目標的複合檔案連線！")
        self.load_history_list()

    def _change_lang(self, lang_code):
        self.current_lang = lang_code
        self.update_ui_language()

    def _open_dir(self, path):
        if os.path.exists(path):
            if platform.system() == "Windows": os.startfile(path)
            elif platform.system() == "Darwin": os.system(f"open '{path}'")

    def _setup_ui(self):
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)

        # ==========================================
        # 左側控制塔
        # ==========================================
        self.left_panel = QFrame()
        self.left_panel.setMinimumWidth(400)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        # 💡 左側收合按鈕 (<) 放在最左邊
        lh = QHBoxLayout()
        self.btn_hide_left = QPushButton("◀")
        self.btn_hide_left.setFixedSize(26, 26)
        self.btn_hide_left.clicked.connect(lambda: self._toggle_panel('left', False))
        lh.addWidget(self.btn_hide_left)
        
        self.lbl_control_title = QLabel("⚙️ 影片下載控制塔")
        lh.addWidget(self.lbl_control_title)
        lh.addStretch()
        
        self.btn_unhide_right = QPushButton("◀")
        self.btn_unhide_right.setFixedSize(26, 26)
        self.btn_unhide_right.clicked.connect(lambda: self._toggle_panel('right', True))
        self.btn_unhide_right.setVisible(False)
        lh.addWidget(self.btn_unhide_right)
        left_layout.addLayout(lh)

        ul = QHBoxLayout()
        self.lbl_url = QLabel("網址:")
        self.url_input = QComboBox()
        self.url_input.setEditable(True)
        self.url_input.addItems(self.loaded_config.get("url_history", []))
        self.btn_analyze = QPushButton("分析 (Analyze)")
        self.btn_analyze.clicked.connect(self.start_parse)
        ul.addWidget(self.lbl_url); ul.addWidget(self.url_input, stretch=1); ul.addWidget(self.btn_analyze)
        left_layout.addLayout(ul)

        ll = QHBoxLayout()
        self.lbl_limit = QLabel("解析限制:")
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(0, 9999)
        self.limit_spin.setValue(self.loaded_config.get("playlist_limit", 0))
        ll.addWidget(self.lbl_limit); ll.addWidget(self.limit_spin); ll.addStretch()
        left_layout.addLayout(ll)

        grid = QFormLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Video", "Audio", "Cover", "Subtitle"])
        
        r_lay = QHBoxLayout()
        self.res_combo = QComboBox(); self.res_combo.addItems(["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"])
        self.vformat_combo = QComboBox(); self.vformat_combo.addItems(["mp4", "mkv"])
        r_lay.addWidget(self.res_combo); r_lay.addWidget(self.vformat_combo)

        a_lay = QHBoxLayout()
        self.audio_res_combo = QComboBox(); self.audio_res_combo.addItems(list(AUDIO_QUALITY_MAP.keys()))
        self.aformat_combo = QComboBox(); self.aformat_combo.addItems(["mp3", "m4a"])
        a_lay.addWidget(self.audio_res_combo); a_lay.addWidget(self.aformat_combo)

        self.lbl_type = QLabel("格式類型:")
        self.lbl_res = QLabel("影片畫質:")
        self.lbl_audio = QLabel("純音訊設定:")
        grid.addRow(self.lbl_type, self.type_combo)
        grid.addRow(self.lbl_res, r_lay)
        grid.addRow(self.lbl_audio, a_lay)
        left_layout.addLayout(grid)

        pl = QHBoxLayout()
        self.lbl_path = QLabel("儲存路徑:")
        self.path_input = QLineEdit()
        self.btn_browse = QPushButton("📂 瀏覽...")
        self.btn_browse.clicked.connect(self.browse_path)
        pl.addWidget(self.lbl_path); pl.addWidget(self.path_input, stretch=1); pl.addWidget(self.btn_browse)
        left_layout.addLayout(pl)

        ol = QHBoxLayout()
        self.chk_embed = QCheckBox("寫入封面圖")
        self.chk_track = QCheckBox("加入音軌序號")
        ol.addWidget(self.chk_embed); ol.addWidget(self.chk_track)
        ol.addStretch()
        left_layout.addLayout(ol)

        sl = QHBoxLayout()
        self.chk_sub = QCheckBox("下載字幕")
        self.chk_sub.setEnabled(False)
        self.sub_combo = QComboBox()
        self.sub_combo.setEnabled(False)
        sl.addWidget(self.chk_sub); sl.addWidget(self.sub_combo); sl.addStretch()
        left_layout.addLayout(sl)

        preview_header = QHBoxLayout()
        self.lbl_preview = QLabel("📥 解析預覽:")
        self.btn_refresh = QPushButton("🔄 重整")
        self.btn_clear = QPushButton("清除")
        self.btn_sel_all = QPushButton("全選")
        self.btn_sel_new = QPushButton("選取新檔")
        self.btn_refresh.clicked.connect(self.refresh_history_in_tree)
        self.btn_clear.clicked.connect(lambda: self._bulk_check(False))
        self.btn_sel_all.clicked.connect(lambda: self._bulk_check(True))
        self.btn_sel_new.clicked.connect(self._select_new)
        
        preview_header.addWidget(self.lbl_preview); preview_header.addStretch()
        preview_header.addWidget(self.btn_refresh); preview_header.addWidget(self.btn_clear)
        preview_header.addWidget(self.btn_sel_all); preview_header.addWidget(self.btn_sel_new)
        left_layout.addLayout(preview_header)

        # Create a splitter to contain the preview tree and the log area
        self.left_inner_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Upper container: Preview Tree
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_tree = QTreeWidget()
        self.preview_tree.setRootIsDecorated(False)
        self.preview_tree.setIndentation(0)
        self.preview_tree.setUniformRowHeights(True)
        self.preview_tree.setStyleSheet("QTreeView::item { padding: 0px; margin: 0px; min-height: 24px; }")
        self.preview_tree.setHeaderLabels(["", "標題 (Title)", "時長", "最後下載 (Last DL)", "網址 (URL)"])
        self.preview_tree.setColumnWidth(0, 24); self.preview_tree.setColumnWidth(1, 230)
        self.preview_tree.setColumnWidth(2, 60); self.preview_tree.setColumnWidth(3, 140)
        self.preview_tree.itemChanged.connect(self.on_item_changed)
        tree_layout.addWidget(self.preview_tree)
        self.left_inner_splitter.addWidget(tree_container)
        
        # Lower container: Progress, Buttons, and Log
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 10, 0, 0)
        
        self.progress_bar = QProgressBar(); self.progress_bar.setValue(0)
        log_layout.addWidget(self.progress_bar)

        bl = QHBoxLayout()
        self.btn_download = QPushButton("⬇ 開始下載")
        self.btn_download.setMinimumHeight(45)
        self.btn_download.clicked.connect(self.start_download)
        self.btn_cancel = QPushButton("❌ 取消")
        self.btn_cancel.setMinimumHeight(45)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_download)
        bl.addWidget(self.btn_download, stretch=2); bl.addWidget(self.btn_cancel, stretch=1)
        log_layout.addLayout(bl)

        self.lbl_log = QLabel("執行紀錄:")
        log_layout.addWidget(self.lbl_log)
        self.log_text = QTextEdit(); self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        self.left_inner_splitter.addWidget(log_container)
        self.left_inner_splitter.setSizes([450, 250]) # Default size ratio
        
        left_layout.addWidget(self.left_inner_splitter, stretch=1)

        # ==========================================
        # 右側歷史長廊
        # ==========================================
        self.right_panel = QFrame()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        
        # 💡 右側收合按鈕 (>) 放在最左邊
        rh = QHBoxLayout()
        self.btn_unhide_left = QPushButton("▶")
        self.btn_unhide_left.setFixedSize(26, 26)
        self.btn_unhide_left.clicked.connect(lambda: self._toggle_panel('left', True))
        self.btn_unhide_left.setVisible(False)
        rh.addWidget(self.btn_unhide_left)

        self.btn_hide_right = QPushButton("▶")
        self.btn_hide_right.setFixedSize(26, 26)
        self.btn_hide_right.clicked.connect(lambda: self._toggle_panel('right', False))
        rh.addWidget(self.btn_hide_right)

        self.lbl_history_title = QLabel("🗃️ 影音歷史資料庫")
        rh.addWidget(self.lbl_history_title)
        rh.addStretch()
        right_layout.addLayout(rh)

        self.tb_layout = QHBoxLayout()
        self.btn_tb_video = QPushButton("🎬影片")
        self.btn_tb_video.setToolTip("下載所選目標之影片")
        self.btn_tb_video.clicked.connect(lambda: self._trigger_history_dl("Video"))
        self.btn_tb_audio = QPushButton("🎵音訊")
        self.btn_tb_audio.setToolTip("下載所選目標之音訊")
        self.btn_tb_audio.clicked.connect(lambda: self._trigger_history_dl("Audio"))
        self.btn_tb_cover = QPushButton("🖼️縮圖")
        self.btn_tb_cover.setToolTip("下載所選目標之縮圖")
        self.btn_tb_cover.clicked.connect(lambda: self._trigger_history_dl("Cover"))
        self.btn_tb_remove = QPushButton("❌刪除列表")
        self.btn_tb_remove.setToolTip("將選取的項目從清單與資料庫中刪除")
        self.btn_tb_remove.clicked.connect(self._remove_selected_history)
        self.btn_tb_clear_dead = QPushButton("🧹清除失效")
        self.btn_tb_clear_dead.setToolTip("找尋遺失檔案並重置其連結紀錄")
        self.btn_tb_clear_dead.clicked.connect(self._clear_dead_history)

        for btn in [self.btn_tb_video, self.btn_tb_audio, self.btn_tb_cover, self.btn_tb_remove, self.btn_tb_clear_dead]:
            self.tb_layout.addWidget(btn)
        self.tb_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜尋標題、頻道、網址...")
        self.search_input.setFixedWidth(180)
        self.search_input.textChanged.connect(self._filter_history)
        self.tb_layout.addWidget(self.search_input)
        
        right_layout.addLayout(self.tb_layout)

        self.history_list = QListWidget()
        self.history_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.history_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.history_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.history_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.history_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self.show_history_context_menu)
        self.history_list.itemSelectionChanged.connect(self._on_history_selection_changed)
        self.history_list.itemDoubleClicked.connect(self._play_history_video)
        self.history_list.setStyleSheet(self.history_list.styleSheet() + " QListWidget::item { border-bottom: 1px solid #E5E7EB; }")
        self.history_list.model().rowsMoved.connect(self._on_history_reordered)
        right_layout.addWidget(self.history_list, stretch=1)

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([500, 800])

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #F8F9FA; }
            QFrame { background-color: #FFFFFF; border-radius: 8px; }
            QLabel { font-weight: bold; color: #374151; font-size: 13px; }
            QLineEdit, QComboBox, QSpinBox { padding: 6px; border: 1px solid #D1D5DB; border-radius: 4px; }
            QPushButton { background-color: #E5E7EB; border: none; padding: 6px 12px; border-radius: 4px; color: #374151; font-weight: bold; }
            QPushButton:hover { background-color: #D1D5DB; }
            QTreeWidget, QListWidget, QTextEdit { border: 1px solid #E5E7EB; border-radius: 4px; background-color: #FFFFFF; }
        """)
        self.btn_download.setStyleSheet("QPushButton { background-color: #10B981; color: white; font-size: 15px; padding: 10px; } QPushButton:hover { background-color: #059669; }")
        self.btn_analyze.setStyleSheet("QPushButton { background-color: #3B82F6; color: white; } QPushButton:hover { background-color: #2563EB; }")
        
        astyle = "QPushButton { background-color: #E5E7EB; border: none; border-radius: 4px; font-size: 14px; color: #374151; } QPushButton:hover { background-color: #D1D5DB; color: #10B981; }"
        for btn in [self.btn_hide_left, self.btn_unhide_left, self.btn_hide_right, self.btn_unhide_right]:
            btn.setStyleSheet(astyle)
            
        if hasattr(self, 'search_input'):
            self.search_input.setStyleSheet("QLineEdit { padding: 4px 8px; border: 1px solid #D1D5DB; border-radius: 4px; font-size: 13px; color: #374151; background-color: #FFF; }")
            
        if hasattr(self, 'btn_tb_video'):
            for btn in [self.btn_tb_video, self.btn_tb_audio, self.btn_tb_cover, self.btn_tb_remove, self.btn_tb_clear_dead]:
                btn.setStyleSheet("QPushButton { background-color: #F3F4F6; border: 1px solid #D1D5DB; border-radius: 4px; padding: 4px 8px; font-size: 13px; color: #374151; font-weight: bold; } QPushButton:hover { background-color: #E5E7EB; }")

    def _restore_settings_to_ui(self):
        cfg = self.loaded_config
        self.path_input.setText(cfg.get("download_path", ""))
        self.res_combo.setCurrentText(cfg.get("video_limit", "1080p"))
        self.vformat_combo.setCurrentText(cfg.get("video_format", "mp4"))
        self.aformat_combo.setCurrentText(cfg.get("audio_format", "mp3"))
        
        aq = cfg.get("audio_quality", "320 kbps (Best)")
        if aq not in AUDIO_QUALITY_MAP:
            aq = REVERSE_AUDIO_QUALITY_MAP.get(aq, "320 kbps (Best)")
        self.audio_res_combo.setCurrentText(aq)
        
        self.chk_embed.setChecked(cfg.get("embed_thumbnail", True))
        self.chk_track.setChecked(cfg.get("add_track_number", True))
        self.chk_sub.setChecked(cfg.get("download_subtitles_enabled", False))

    def update_ui_language(self):
        lang = I18N.get(self.current_lang, I18N["zh-TW"])
        self.lbl_url.setText(lang["url"])
        self.btn_analyze.setText(lang["analyze"])
        self.lbl_limit.setText(lang["limit"])
        self.lbl_type.setText(lang["type"])
        self.lbl_res.setText(lang["res"])
        self.lbl_audio.setText(lang["audio"])
        self.lbl_path.setText(lang["path"])
        self.btn_browse.setText(lang["browse"])
        self.chk_embed.setText(lang["embed_thumb"])
        self.chk_track.setText(lang["add_track"])
        self.chk_sub.setText(lang["dl_subtitles"])
        self.lbl_preview.setText(lang["preview"])
        self.btn_refresh.setText(lang["refresh"])
        self.btn_clear.setText(lang["clear"])
        self.btn_sel_all.setText(lang["select_all"])
        self.btn_sel_new.setText(lang["select_new"])
        self.btn_download.setText("⬇ " + lang["download"])
        self.btn_cancel.setText("❌ " + lang["cancel"])
        self.lbl_log.setText(lang["log"])
        
        self.preview_tree.setHeaderLabels(["", lang["col_title"], lang["col_duration"], lang["col_lastdl"], lang["col_url"]])
        self.loaded_config["language"] = self.current_lang
        
        if hasattr(self, 'file_menu'):
            self.file_menu.setTitle(lang.get("menu_file", ""))
            self.open_folder_action.setText(lang.get("action_open_dl", ""))
            self.exit_action.setText(lang.get("action_exit", ""))
            self.settings_menu.setTitle(lang.get("menu_settings", ""))
            self.save_settings_action.setText(lang.get("action_save_cfg", ""))
            if hasattr(self, 'dl_organize_action'):
                self.dl_organize_action.setText(lang.get("action_dl_organize", ""))
            self.lang_menu.setTitle(lang.get("menu_lang", ""))
            self.action_tw.setText(lang.get("action_tw", ""))
            self.action_en.setText(lang.get("action_en", ""))
            self.action_ja.setText(lang.get("action_ja", ""))
            self.tools_menu.setTitle(lang.get("menu_tools", ""))
            self.import_json_action.setText(lang.get("action_import_json", ""))
            self.fetch_meta_action.setText(lang.get("action_fetch_meta", ""))
            self.scan_all_action.setText(lang.get("action_scan_all", ""))
            
        if hasattr(self, 'lbl_control_title'):
            self.lbl_control_title.setText(lang.get("lbl_control_title", ""))
            if hasattr(self, 'lbl_history_title'):
                self.lbl_history_title.setText(lang.get("lbl_history_title", ""))
                
        if hasattr(self, 'btn_tb_video'):
            self.btn_tb_video.setText(lang.get("tb_video", ""))
            self.btn_tb_audio.setText(lang.get("tb_audio", ""))
            self.btn_tb_cover.setText(lang.get("tb_cover", ""))
            self.btn_tb_remove.setText(lang.get("tb_remove", ""))
            self.btn_tb_clear_dead.setText(lang.get("tb_clear_dead", ""))
            if hasattr(self, 'search_input'):
                self.search_input.setPlaceholderText(lang.get("ph_search", ""))

    def log_msg(self, msg):
        self.log_text.append(f"{datetime.now().strftime('%H:%M:%S')} - {msg}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def browse_path(self):
        d = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if d: self.path_input.setText(d)

    def _toggle_panel(self, panel_name, show):
        if panel_name == 'left':
            self.left_panel.setVisible(show)
            self.btn_unhide_left.setVisible(not show)
            self.btn_hide_right.setEnabled(show)
        elif panel_name == 'right':
            self.right_panel.setVisible(show)
            self.btn_unhide_right.setVisible(not show)
            self.btn_hide_left.setEnabled(show)

    # 💡 真正的 PyQt6 Checkbox 邏輯
    def _bulk_check(self, state):
        for i in range(self.preview_tree.topLevelItemCount()):
            item = self.preview_tree.topLevelItem(i)
            widget = self.preview_tree.itemWidget(item, 0)
            if widget and widget.layout().itemAt(0).widget(): widget.layout().itemAt(0).widget().setChecked(state)

    def _select_new(self):
        for i in range(self.preview_tree.topLevelItemCount()):
            item = self.preview_tree.topLevelItem(i)
            widget = self.preview_tree.itemWidget(item, 0)
            if widget and widget.layout().itemAt(0).widget(): widget.layout().itemAt(0).widget().setChecked(item.text(3) == "Not Downloaded")

    def on_item_changed(self, item, column):
        if column == 0: self.update_subtitle_controls()

    def update_subtitle_controls(self):
        all_langs = set()
        for i in range(self.preview_tree.topLevelItemCount()):
            item = self.preview_tree.topLevelItem(i)
            widget = self.preview_tree.itemWidget(item, 0)
            chk = widget.layout().itemAt(0).widget() if widget else None
            if chk and chk.isChecked():
                sub_langs = item.data(0, Qt.ItemDataRole.UserRole)[7] 
                if sub_langs:
                    try: all_langs.update(json.loads(sub_langs))
                    except: pass
        
        is_sub_mode = self.type_combo.currentText() == "Subtitle"
        if all_langs:
            self.sub_combo.setEnabled(True)
            langs_list = ["all"] + sorted(list(all_langs))
            self.sub_combo.clear(); self.sub_combo.addItems(langs_list)
            if "zh-TW" in langs_list: self.sub_combo.setCurrentText("zh-TW")
            
            if is_sub_mode:
                self.chk_sub.setChecked(True); self.chk_sub.setEnabled(False)
            else:
                self.chk_sub.setEnabled(True)
        else:
            self.chk_sub.setChecked(False); self.chk_sub.setEnabled(False)
            self.sub_combo.clear(); self.sub_combo.setEnabled(False)

    def refresh_history_in_tree(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for i in range(self.preview_tree.topLevelItemCount()):
            item = self.preview_tree.topLevelItem(i)
            video_id = item.data(0, Qt.ItemDataRole.UserRole)[2]
            cursor.execute("SELECT download_time FROM downloads WHERE video_id = ?", (video_id,))
            row = cursor.fetchone()
            if row: item.setText(3, row[0])
        conn.close()
        lang_dict = I18N.get(self.current_lang, I18N["zh-TW"])
        self.log_msg(lang_dict.get("log_refresh", "紀錄已重整。"))

    def start_parse(self):
        url = self.url_input.currentText().strip()
        if not url: return self.log_msg("請輸入網址。")
        
        history = self.loaded_config.get("url_history", [])
        if url in history: history.remove(url)
        history.insert(0, url)
        self.loaded_config["url_history"] = history[:20]
        self._save_config()
        if self.url_input.findText(url) == -1: self.url_input.insertItem(0, url)
            
        self.preview_tree.clear()
        self.btn_analyze.setEnabled(False)
        self.parse_worker = ParseWorker(url, self.limit_spin.value(), I18N.get(self.current_lang, I18N["zh-TW"]))
        self.parse_worker.log_signal.connect(self.log_msg)
        self.parse_worker.item_signal.connect(self.add_tree_item)
        self.parse_worker.finished_signal.connect(lambda: [self.btn_analyze.setEnabled(True), self.refresh_history_in_tree(), self.update_subtitle_controls()])
        self.parse_worker.start()

    def add_tree_item(self, idx, entry, ctype, ptitle, channel):
        video_id = entry.get("id", "")
        title = sanitize_filename(entry.get("title", "Unknown"))
        url = entry.get("webpage_url") or entry.get("url") or "N/A"
        duration = entry.get("duration")
        dur_text = f"{int(duration)//60:02d}:{int(duration)%60:02d}" if duration else "Unknown"
        subtitles = entry.get("subtitles"); sub_langs = json.dumps(list(subtitles.keys())) if subtitles else "[]"
        
        # 💡 PyQt6 原生 Checkbox 設置
        item = QTreeWidgetItem(["", title, dur_text, "Not Downloaded", url])
        item.setData(0, Qt.ItemDataRole.UserRole, (url, title, video_id, ctype, ptitle, channel, entry.get('playlist_index', ''), sub_langs, dur_text))
        self.preview_tree.addTopLevelItem(item)
        chk = QCheckBox()
        chk.setChecked(True)
        chk.stateChanged.connect(lambda state: self.update_subtitle_controls())
        # Wrap strictly to zero out annoying wide margins and center it precisely
        widget = QWidget()
        lay = QHBoxLayout(widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(chk, alignment=Qt.AlignmentFlag.AlignCenter)
        widget.setFixedHeight(24)
        self.preview_tree.setItemWidget(item, 0, widget)

    def start_download(self):
        items = []
        for i in range(self.preview_tree.topLevelItemCount()):
            item = self.preview_tree.topLevelItem(i)
            # 💡 根據原生 Checkbox 狀態判斷
            widget = self.preview_tree.itemWidget(item, 0)
            chk = widget.layout().itemAt(0).widget() if widget else None
            if chk and chk.isChecked(): 
                items.append(item.data(0, Qt.ItemDataRole.UserRole))
        
        if not items: return self.log_msg("請選擇要下載的項目。")

        settings = {
            'type': self.type_combo.currentText(), 'path': self.path_input.text(),
            'res': self.res_combo.currentText(), 'v_format': self.vformat_combo.currentText(),
            'a_res': self.audio_res_combo.currentText(), 'a_format': self.aformat_combo.currentText(),
            'embed_thumb': self.chk_embed.isChecked(), 'add_track': self.chk_track.isChecked(),
            'dl_sub': self.chk_sub.isChecked(), 'sub_lang': self.sub_combo.currentText(),
            'organize_by_channel': self.loaded_config.get('organize_by_channel', True),
            'organize_by_type': self.loaded_config.get('organize_by_type', True)
        }

        self.btn_download.setEnabled(False); self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)
        
        self.dl_worker = DownloadWorker(settings, items, i18n_dict=I18N.get(self.current_lang, I18N["zh-TW"]))
        self.dl_worker.log_signal.connect(self.log_msg)
        self.dl_worker.progress_signal.connect(self.progress_bar.setValue)
        self.dl_worker.finished_signal.connect(self._dl_finished)
        self.dl_worker.start()

    def _trigger_history_dl(self, dl_type):
        selected = self.history_list.selectedItems()
        if not selected: return self.log_msg("⚠️ 請先在歷史列表中選擇要操作的項目。")
        records = []
        for item in selected:
            w = self.history_list.itemWidget(item)
            if w and hasattr(w, 'record'): records.append(w.record)
        self._start_batch_direct_download(records, dl_type)

    def _start_batch_direct_download(self, records, dl_type):
        items = []
        for record in records:
            url = record.get('url', '')
            if not url: continue
            fp = record.get('filepath')
            dl_path = os.path.dirname(fp) if fp and os.path.exists(os.path.dirname(fp)) else self.path_input.text()
            
            items.append((
                url, record.get('title', 'Unknown'), record.get('video_id', ''), "video",
                "", record.get('channel', 'Unknown'), "", "[]", record.get('duration', '00:00'), dl_path
            ))
            
        if not items: return self.log_msg("⚠️ 沒有有效的網址可供獨立下載。")
        
        settings = {
            'type': dl_type, 'path': self.path_input.text(),
            'res': self.res_combo.currentText(), 'v_format': self.vformat_combo.currentText(),
            'a_res': self.audio_res_combo.currentText(), 'a_format': self.aformat_combo.currentText(),
            'embed_thumb': self.chk_embed.isChecked(), 'add_track': False,
            'dl_sub': self.chk_sub.isChecked(), 'sub_lang': self.sub_combo.currentText()
        }
        
        self.btn_download.setEnabled(False); self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)
        self.dl_worker = DownloadWorker(settings, items, exact_path=True, i18n_dict=I18N.get(self.current_lang, I18N["zh-TW"]))
        self.dl_worker.log_signal.connect(self.log_msg)
        self.dl_worker.progress_signal.connect(self.progress_bar.setValue)
        self.dl_worker.finished_signal.connect(self._dl_finished)
        self.dl_worker.start()

    def cancel_download(self):
        if hasattr(self, 'dl_worker'): self.dl_worker.cancel()
        self.log_msg("取消中...")

    def _dl_finished(self):
        self.btn_download.setEnabled(True); self.btn_cancel.setEnabled(False)
        self.refresh_history_in_tree()
        self.load_history_list()
        
    def _filter_history(self, text):
        text = text.lower()
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            w = self.history_list.itemWidget(item)
            if w and hasattr(w, 'record'):
                rec = w.record
                title = (rec.get('title') or '').lower()
                channel = (rec.get('channel') or '').lower()
                url = (rec.get('url') or '').lower()
                if not text or text in title or text in channel or text in url:
                    item.setHidden(False)
                else:
                    item.setHidden(True)

    def load_history_list(self):
        v_scroll = self.history_list.verticalScrollBar().value()
        h_scroll = self.history_list.horizontalScrollBar().value()
        
        selected_vids = set()
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            if item.isSelected():
                w = self.history_list.itemWidget(item)
                if w and w.record.get('video_id'):
                    selected_vids.add(w.record.get('video_id'))
                    
        self.history_list.clear()
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM downloads ORDER BY CASE WHEN sort_order IS NOT NULL THEN 0 ELSE 1 END, sort_order ASC, download_time DESC")
            
            self.history_list.setUpdatesEnabled(False)
            for row in cursor.fetchall():
                record = dict(row)
                item = QListWidgetItem(self.history_list)
                widget = HistoryCardWidget(record, self)
                item.setSizeHint(QSize(0, 80))
                self.history_list.setItemWidget(item, widget)
                
                if record.get('video_id') in selected_vids:
                    item.setSelected(True)
            self.history_list.setUpdatesEnabled(True)
            
            self.history_list.verticalScrollBar().setValue(v_scroll)
            self.history_list.horizontalScrollBar().setValue(h_scroll)
            conn.close()
        except Exception as e:
            self.history_list.setUpdatesEnabled(True)
            self.log_msg(f"讀取歷史紀錄失敗: {e}")

    def _remove_selected_history(self):
        selected = self.history_list.selectedItems()
        if not selected: return self.log_msg("⚠️ 請先在歷史列表中選擇要移除的項目。")
        conn = sqlite3.connect(DB_PATH)
        for item in selected:
            w = self.history_list.itemWidget(item)
            if w and w.record.get('video_id'):
                conn.execute("DELETE FROM downloads WHERE video_id=?", (w.record['video_id'],))
        conn.commit(); conn.close()
        self.load_history_list()
        self.log_msg(f"✅ 已從歷史清單與資料庫中徹底移除 {len(selected)} 筆紀錄。")

    def _clear_dead_history(self):
        self.log_msg("🔍 正在背景掃描全資料庫驗證實體檔案路徑...")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT video_id, filepath FROM downloads WHERE filepath IS NOT NULL AND filepath != ''")
        dead_vids = []
        for row in cursor.fetchall():
            fp_str = row['filepath']
            all_dead = all(not os.path.exists(f) for f in fp_str.split('|') if f)
            if all_dead: dead_vids.append(row['video_id'])
                
        if dead_vids:
            chunked = [dead_vids[i:i+900] for i in range(0, len(dead_vids), 900)]
            for chunk in chunked:
                conn.execute(f"UPDATE downloads SET filepath=NULL WHERE video_id IN ({','.join(['?']*len(chunk))})", chunk)
            self.log_msg(f"✅ 掃除完畢！已將 {len(dead_vids)} 筆「實體檔案遺失」的紀錄路徑重置，您可隨時利用原地補齊重新下載。")
        else:
            self.log_msg("✅ 掃除完畢！所有實體檔案皆完好存在，無需還原。")
            
        conn.commit(); conn.close()
        self.load_history_list()

        
    def _play_history_video(self, item):
        widget = self.history_list.itemWidget(item)
        if widget:
            fp = widget.current_fp or ''
            if fp and os.path.exists(fp):
                if platform.system() == "Windows": os.startfile(fp)
                elif platform.system() == "Darwin": os.system(f"open '{fp}'")
            else:
                record = widget.record
                channel = sanitize_filename(record.get('channel', '')) if record.get('channel') else ''
                ch_dir = os.path.join(self.path_input.text(), channel) if channel else ''
                if ch_dir and os.path.isdir(ch_dir):
                    os.startfile(ch_dir)
                    self.log_msg(f"⚠️ 檔案遺失，已開啟頻道目錄: {ch_dir}")
                else:
                    fallback = self.path_input.text() or BASE_DIR
                    if os.path.isdir(fallback): os.startfile(fallback)
                    self.log_msg(f"⚠️ 檔案遺失，已開啟下載目錄: {fallback}")

    def _on_history_reordered(self):
        conn = sqlite3.connect(DB_PATH)
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            w = self.history_list.itemWidget(item)
            if w and w.record.get('video_id'):
                conn.execute("UPDATE downloads SET sort_order=? WHERE video_id=?", (i, w.record['video_id']))
        conn.commit(); conn.close()

    def _on_history_selection_changed(self):
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            widget = self.history_list.itemWidget(item)
            if widget:
                is_sel = item.isSelected()
                widget.setStyleSheet("#historyCard { background-color: #EBF5FF; border-radius: 4px; }" if is_sel else "#historyCard { background-color: transparent; }")

    def show_history_context_menu(self, pos):
        item = self.history_list.itemAt(pos)
        if not item: return
        widget = self.history_list.itemWidget(item)
        if not widget: return
        record = widget.record
        lang = I18N.get(self.current_lang, I18N["zh-TW"])
        
        menu = QMenu()
        a_folder = menu.addAction(lang["ctx_folder"])
        a_copy = menu.addAction(lang["ctx_copy"])
        a_open = menu.addAction(lang["ctx_browser"])
        menu.addSeparator()
        a_fetch = menu.addAction(lang["ctx_fetch"])
        a_scan_silent = menu.addAction(lang["ctx_scan_silent"])
        a_scan_custom = menu.addAction(lang["ctx_scan_custom"])
        
        dl_menu = menu.addMenu(lang["ctx_dl"])
        a_dl_channel = dl_menu.addAction(lang["ctx_dl_channel"])
        a_dl_video = dl_menu.addAction(lang["ctx_dl_video"])
        a_dl_audio = dl_menu.addAction(lang["ctx_dl_audio"])
        a_dl_cover = dl_menu.addAction(lang["ctx_dl_cover"])
        
        menu.addSeparator()
        a_remove = menu.addAction(lang["ctx_remove"])
        a_delete = menu.addAction(lang["ctx_delete"])
        a_clear = menu.addAction(lang["ctx_clear"])
        
        action = menu.exec(self.history_list.mapToGlobal(pos))
        if action == a_folder:
            fp = widget.current_fp or ''
            folder = os.path.dirname(fp) if fp else ''
            if folder and os.path.exists(folder):
                os.startfile(folder)
            else:
                channel = sanitize_filename(record.get('channel', '')) if record.get('channel') else ''
                ch_dir = os.path.join(self.path_input.text(), channel) if channel else ''
                if ch_dir and os.path.isdir(ch_dir):
                    os.startfile(ch_dir)
                else:
                    fallback = self.path_input.text() or BASE_DIR
                    if os.path.isdir(fallback): os.startfile(fallback)
        elif action == a_copy:
            QApplication.clipboard().setText(record.get('url', ''))
        elif action == a_open:
            webbrowser.open(record.get('url', ''))
        elif action == a_fetch:
            selected = self.history_list.selectedItems()
            if not selected: selected = [item]
            tasks = []
            for sel_item in selected:
                w = self.history_list.itemWidget(sel_item)
                if w and w.record.get('video_id') and w.record.get('url'):
                    tasks.append((w.record.get('video_id'), w.record.get('url')))
            if tasks:
                self.log_msg(f"🔍 開始背景補齊 {len(tasks)} 筆影片資訊...")
                worker = MetadataWorker(tasks)
                worker.update_signal.connect(self._update_single_card)
                worker.progress_signal.connect(self.log_msg)
                worker.finished_signal.connect(lambda: self.log_msg(f"✅ 所選之 {len(tasks)} 筆資訊補齊作業完成。"))
                if not hasattr(self, 'meta_workers'): self.meta_workers = []
                self.meta_workers.append(worker)
                worker.finished_signal.connect(lambda w=worker: self.meta_workers.remove(w) if w in self.meta_workers else None)
                worker.start()
        elif action == a_scan_silent:
            selected = self.history_list.selectedItems()
            if not selected: selected = [item]
            self.run_local_scan(selected, silent=True)
        elif action == a_scan_custom:
            vid = record.get('video_id')
            if not vid: return
            channel = sanitize_filename(record.get('channel', '')) if record.get('channel') else ''
            start_dir = os.path.join(self.path_input.text(), channel) if channel and os.path.isdir(os.path.join(self.path_input.text(), channel)) else self.path_input.text()
            fp, _ = QFileDialog.getOpenFileName(self, "選擇檔案位置", start_dir, "Media Files (*.mp4 *.mkv *.webm *.m4a *.mp3 *.m4v *.opus *.flac *.wav *.srt *.vtt *.jpg *.webp *.png);;All Files (*)")
            if fp:
                fp = os.path.normpath(fp)
                ext = fp.split('.')[-1].lower()
                size_bytes = os.path.getsize(fp)
                filesize = f"{size_bytes/(1024*1024*1024):.1f} GB" if size_bytes >= 1024**3 else f"{size_bytes/(1024*1024):.1f} MB" if size_bytes >= 1024**2 else f"{size_bytes/1024:.1f} KB"
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT filepath, format, filesize FROM downloads WHERE video_id=?", (vid,))
                existing = cur.fetchone()
                if existing and existing['filepath']:
                    old_fps = [f for f in existing['filepath'].split('|') if f]
                    old_fmts = [f for f in (existing['format'] or '').split('|') if f]
                    old_fss = [s for s in (existing['filesize'] or '').split('|') if s]
                    if fp not in old_fps:
                        old_fps.append(fp); old_fmts.append(ext); old_fss.append(filesize)
                    conn.execute("UPDATE downloads SET filepath=?, format=?, filesize=? WHERE video_id=?",
                                 ('|'.join(old_fps), '|'.join(old_fmts), '|'.join(old_fss), vid))
                else:
                    conn.execute("UPDATE downloads SET filepath=?, format=?, filesize=? WHERE video_id=?",
                                 (fp, ext, filesize, vid))
                conn.commit(); conn.close()
                self.log_msg(f"✅ 已手動綁定檔案: {os.path.basename(fp)}")
                self.load_history_list()
        elif action == a_dl_channel:
            self.url_input.setCurrentText(f"https://www.youtube.com/@{record.get('channel', 'Unknown')}/videos")
            self.start_parse()
        elif action == a_dl_video:
            self._start_batch_direct_download([record], "Video")
        elif action == a_dl_audio:
            self._start_batch_direct_download([record], "Audio")
        elif action == a_dl_cover:
            self._start_batch_direct_download([record], "Cover")
        elif action == a_remove:
            selected = self.history_list.selectedItems()
            if not selected: selected = [item]
            for sel_item in selected:
                w = self.history_list.itemWidget(sel_item)
                if w: self._remove_history_db(w.record.get('video_id', ''))
            self.load_history_list()
        elif action == a_delete:
            selected = self.history_list.selectedItems()
            if not selected: selected = [item]
            
            dialog = QDialog(self)
            dialog.setWindowTitle("確定要刪除檔案嗎？")
            d_lay = QVBoxLayout(dialog)
            d_lay.addWidget(QLabel(f"即將刪除 {len(selected)} 個已選取項目的實體檔案與歷史資料庫紀錄。"))
            chk_trash = QCheckBox("丟入資源回收桶 (如支援)")
            chk_trash.setChecked(True)
            d_lay.addWidget(chk_trash)
            bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            bbox.accepted.connect(dialog.accept)
            bbox.rejected.connect(dialog.reject)
            d_lay.addWidget(bbox)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                for sel_item in selected:
                    w = self.history_list.itemWidget(sel_item)
                    if not w: continue
                    fp = w.record.get('filepath', '')
                    if fp and os.path.exists(fp):
                        try:
                            if chk_trash.isChecked():
                                try:
                                    import send2trash
                                    send2trash.send2trash(fp)
                                except: os.remove(fp)
                            else: os.remove(fp)
                        except: pass
                    
                    tp = w.record.get('thumbnail_path', '')
                    if tp and os.path.exists(tp):
                        try: os.remove(tp)
                        except: pass
                    self._remove_history_db(w.record.get('video_id', ''))
                self.load_history_list()

        elif action == a_clear:
            reply = QDialog(self)
            reply.setWindowTitle("警告")
            vlay = QVBoxLayout(reply)
            vlay.addWidget(QLabel("確定要清空全部分析與下載歷史紀錄嗎？\n(此動作不會刪除硬碟中的實體檔案)"))
            btnbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No)
            btnbox.accepted.connect(reply.accept)
            btnbox.rejected.connect(reply.reject)
            vlay.addWidget(btnbox)
            if reply.exec() == QDialog.DialogCode.Accepted:
                conn = sqlite3.connect(DB_PATH)
                conn.execute("DELETE FROM downloads")
                conn.commit(); conn.close()
                self.load_history_list()

    def _remove_history_db(self, video_id):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM downloads WHERE video_id=?", (video_id,))
        conn.commit(); conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())