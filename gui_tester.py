import sys
import os
import json
import time
import urllib.request
import urllib.error
import re
import base64
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal, Slot, QUrl
from PySide6.QtGui import QFont, QIcon, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
    QCheckBox, QSplitter, QFrame, QGroupBox, QMessageBox, QFileDialog
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

MEDIA_DIR = r"H:\reqble-mcp\media"
os.makedirs(MEDIA_DIR, exist_ok=True)

DARK_STYLESHEET = """
QMainWindow {
    background-color: #121316;
}
QWidget {
    color: #e3e3e3;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #2d3139;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 12px;
    font-weight: bold;
    color: #9aa0a6;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QLineEdit, QComboBox, QTextEdit {
    background-color: #1e2025;
    border: 1px solid #333842;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f1f3f4;
    selection-background-color: #1a73e8;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #1a73e8;
}
QPushButton {
    background-color: #1a73e8;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1557b0;
}
QPushButton:pressed {
    background-color: #0d47a1;
}
QPushButton#stopBtn {
    background-color: #d93025;
}
QPushButton#stopBtn:hover {
    background-color: #b3261e;
}
QPushButton#mediaBtn {
    background-color: #1e8e3e;
}
QPushButton#mediaBtn:hover {
    background-color: #188038;
}
QPushButton#clearBtn {
    background-color: #2b303c;
    color: #bdc1c6;
}
QPushButton#clearBtn:hover {
    background-color: #3c4043;
}
QCheckBox {
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #4a505c;
    background: #1e2025;
}
QCheckBox::indicator:checked {
    background: #1a73e8;
    border-color: #1a73e8;
}
"""

CHAT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {
  background-color: #121316;
  color: #e3e3e3;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  padding: 16px;
  margin: 0;
  line-height: 1.6;
}
.message {
  margin-bottom: 22px;
  animation: fadeIn 0.25s ease-in-out;
}
.role-user {
  color: #8ab4f8;
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 6px;
}
.role-ai {
  color: #81c995;
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 6px;
}
.content {
  background-color: #1a1c22;
  border: 1px solid #2b2e38;
  border-radius: 8px;
  padding: 14px 18px;
  word-wrap: break-word;
  white-space: pre-wrap;
}
.media-wrapper {
  margin: 12px 0;
}
img.generated-media {
  max-width: 95%;
  max-height: 520px;
  border-radius: 10px;
  border: 1px solid #3c4043;
  box-shadow: 0 4px 16px rgba(0,0,0,0.5);
  display: block;
}
video.generated-video {
  max-width: 95%;
  max-height: 520px;
  border-radius: 10px;
  border: 1px solid #3c4043;
  box-shadow: 0 4px 16px rgba(0,0,0,0.5);
  display: block;
}
.media-caption {
  font-size: 12px;
  color: #9aa0a6;
  margin-top: 6px;
  font-style: italic;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
</head>
<body>
<div id="chat-container"></div>
<script>
function appendUserMessage(text) {
  const c = document.getElementById('chat-container');
  const d = document.createElement('div');
  d.className = 'message';
  d.innerHTML = '<div class="role-user">[You]</div><div class="content">' + escapeHtml(text) + '</div>';
  c.appendChild(d);
  window.scrollTo(0, document.body.scrollHeight);
}

function startAiMessage() {
  const c = document.getElementById('chat-container');
  const d = document.createElement('div');
  d.className = 'message';
  d.innerHTML = '<div class="role-ai">[AI Assistant]</div><div class="content" id="active-ai-content"></div>';
  c.appendChild(d);
  window.scrollTo(0, document.body.scrollHeight);
}

function updateAiContent(htmlContent) {
  const el = document.getElementById('active-ai-content');
  if (el) {
    el.innerHTML = htmlContent;
    window.scrollTo(0, document.body.scrollHeight);
  }
}

function finalizeAiMessage() {
  const el = document.getElementById('active-ai-content');
  if (el) el.removeAttribute('id');
  window.scrollTo(0, document.body.scrollHeight);
}

function clearChat() {
  document.getElementById('chat-container').innerHTML = '';
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
</script>
</body>
</html>
"""

class RequestWorker(QThread):
    chunk_received = Signal(str)
    finished_signal = Signal(str, float)
    error_signal = Signal(str)

    def __init__(self, url, api_key, model, prompt, is_stream):
        super().__init__()
        self.url = url
        self.api_key = api_key
        self.model = model
        self.prompt = prompt
        self.is_stream = is_stream
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        t_start = time.time()
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": self.prompt}],
            "stream": self.is_stream
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            req = urllib.request.Request(
                self.url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=120) as resp:
                if not self.is_stream:
                    res_body = resp.read().decode("utf-8")
                    data = json.loads(res_body)
                    ans = data["choices"][0]["message"].get("content", "")
                    elapsed = time.time() - t_start
                    self.finished_signal.emit(ans, elapsed)
                    return

                # Streaming mode
                full_text = ""
                for line in resp:
                    if self._is_cancelled:
                        break
                    line_str = line.decode("utf-8").strip()
                    if not line_str.startswith("data: "):
                        continue
                    raw = line_str[6:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(raw)
                        delta = chunk_json["choices"][0]["delta"].get("content", "")
                        if delta:
                            full_text += delta
                            self.chunk_received.emit(delta)
                    except Exception:
                        pass

                elapsed = time.time() - t_start
                self.finished_signal.emit(full_text, elapsed)

        except urllib.error.HTTPError as e:
            err_msg = f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"
            self.error_signal.emit(err_msg)
        except Exception as e:
            self.error_signal.emit(str(e))


class ApiTesterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Reverse Proxy Gateway - PySide6 WebEngine Media Viewer")
        self.resize(1150, 850)
        self.worker = None
        self.accumulated_text = ""
        self.saved_media_map = {}

        self.init_ui()
        self.apply_preset_target(0)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # Config Panel
        config_box = QGroupBox("Cấu hình kết nối API")
        config_layout = QHBoxLayout(config_box)
        config_layout.setSpacing(10)

        # Preset Selector
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "DeepSeek - R1 Reasoner (Port 3000)",
            "DeepSeek - V3 Chat (Port 3000)",
            "Google Gemini Web (Port 3000)",
            "ChatGPT GPT-4o (Port 3000)",
            "Tùy chỉnh Endpoint..."
        ])
        self.preset_combo.currentIndexChanged.connect(self.apply_preset_target)

        # URL Input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://localhost:3000/v1/chat/completions")

        # API Key Input
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("API Key (Bearer token)")

        # Model Input
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Model name (vd: gemini-web)")

        # Stream Checkbox
        self.stream_check = QCheckBox("Stream (SSE)")
        self.stream_check.setChecked(True)

        config_layout.addWidget(QLabel("Cổng:"))
        config_layout.addWidget(self.preset_combo, 2)
        config_layout.addWidget(QLabel("URL:"))
        config_layout.addWidget(self.url_input, 4)
        config_layout.addWidget(QLabel("Key:"))
        config_layout.addWidget(self.key_input, 2)
        config_layout.addWidget(QLabel("Model:"))
        config_layout.addWidget(self.model_input, 2)
        config_layout.addWidget(self.stream_check, 1)

        main_layout.addWidget(config_box)

        # QWebEngineView for rich HTML5 Media rendering (Images, Videos, Markdown)
        self.web_view = QWebEngineView()
        self.web_view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        self.web_view.settings().setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        self.web_view.setHtml(CHAT_HTML_TEMPLATE)
        main_layout.addWidget(self.web_view, 1)

        # Input & Actions Area
        input_box = QGroupBox("Gửi Prompt Thử Nghiệm")
        input_layout = QVBoxLayout(input_box)
        input_layout.setSpacing(8)

        # Prompt presets toolbar
        preset_bar = QHBoxLayout()
        preset_bar.addWidget(QLabel("Gợi ý:"))

        sample_prompts = [
            "tạo hình một trái chuối biết bay",
            "Hỏi model đang dùng",
            "1 + 1 bằng mấy?",
            "Viết hàm Python tính fibonacci",
            "Giải thích định lý Fermat"
        ]
        for p in sample_prompts:
            btn = QPushButton(p)
            btn.setStyleSheet("background-color: #262930; color: #8ab4f8; font-weight: normal; padding: 4px 10px;")
            btn.clicked.connect(lambda _, text=p: self.insert_sample_prompt(text))
            preset_bar.addWidget(btn)

        preset_bar.addStretch()

        self.media_folder_btn = QPushButton("Mở Thư Mục Media")
        self.media_folder_btn.setObjectName("mediaBtn")
        self.media_folder_btn.clicked.connect(self.open_media_folder)
        preset_bar.addWidget(self.media_folder_btn)

        self.clear_btn = QPushButton("Xóa Chat")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self.clear_chat_ui)
        preset_bar.addWidget(self.clear_btn)

        input_layout.addLayout(preset_bar)

        # Text input & send button
        bottom_bar = QHBoxLayout()
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Nhập câu hỏi hoặc prompt tại đây (Ctrl+Enter để gửi)...")
        self.prompt_input.setMaximumHeight(80)

        btn_layout = QVBoxLayout()
        self.send_btn = QPushButton("Gửi (Send)")
        self.send_btn.setMinimumHeight(40)
        self.send_btn.clicked.connect(self.send_request)

        self.stop_btn = QPushButton("Dừng (Stop)")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_request)

        btn_layout.addWidget(self.send_btn)
        btn_layout.addWidget(self.stop_btn)

        bottom_bar.addWidget(self.prompt_input, 1)
        bottom_bar.addLayout(btn_layout)

        input_layout.addLayout(bottom_bar)
        main_layout.addWidget(input_box)

        # Status Bar
        self.status_label = QLabel("Sẵn sàng. Thư mục lưu media: " + MEDIA_DIR)
        self.status_label.setStyleSheet("color: #9aa0a6; font-size: 11px;")
        main_layout.addWidget(self.status_label)

    def apply_preset_target(self, idx):
        if idx == 0:
            self.url_input.setText("http://localhost:3000/v1/chat/completions")
            self.key_input.setText("sk-unified-local-gateway-key")
            self.model_input.setText("deepseek-reasoner")
        elif idx == 1:
            self.url_input.setText("http://localhost:3000/v1/chat/completions")
            self.key_input.setText("sk-unified-local-gateway-key")
            self.model_input.setText("deepseek-chat")
        elif idx == 2:
            self.url_input.setText("http://localhost:3000/v1/chat/completions")
            self.key_input.setText("sk-unified-local-gateway-key")
            self.model_input.setText("gemini-web")
        elif idx == 3:
            self.url_input.setText("http://localhost:3000/v1/chat/completions")
            self.key_input.setText("sk-unified-local-gateway-key")
            self.model_input.setText("gpt-4o")

    def insert_sample_prompt(self, text):
        if text == "Hỏi model đang dùng":
            self.prompt_input.setPlainText("Hiện tại bạn là phiên bản mô hình AI cụ thể nào? Hãy trả lời ngắn gọn.")
        else:
            self.prompt_input.setPlainText(text)

    def open_media_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(MEDIA_DIR))

    def clear_chat_ui(self):
        self.web_view.page().runJavaScript("clearChat();")

    def format_media_html(self, text):
        """Parse text, extract base64 images/videos, auto-save to disk, and format as HTML5."""
        # 1. Handle Markdown Images: ![alt](url)
        def replace_img(match):
            alt = match.group(1)
            src = match.group(2)
            
            # If data URL or HTTP URL, save file to disk once
            saved_hint = ""
            display_src = src
            if src in self.saved_media_map:
                filename, local_url = self.saved_media_map[src]
                display_src = local_url
                saved_hint = f"<br/><span style='color: #81c995; font-size: 11px;'>[Đã lưu: {filename}]</span>"
            elif src.startswith("data:image/"):
                try:
                    ext = "png"
                    if "image/jpeg" in src: ext = "jpg"
                    elif "image/webp" in src: ext = "webp"
                    b64_data = src.split(",", 1)[1]
                    filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}.{ext}"
                    filepath = os.path.join(MEDIA_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(b64_data))
                    local_url = QUrl.fromLocalFile(filepath).toString()
                    self.saved_media_map[src] = (filename, local_url)
                    display_src = local_url
                    saved_hint = f"<br/><span style='color: #81c995; font-size: 11px;'>[Đã lưu: {filename}]</span>"
                except Exception:
                    pass
            elif src.startswith("http://") or src.startswith("https://"):
                try:
                    ext = "jpg"
                    filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}.{ext}"
                    filepath = os.path.join(MEDIA_DIR, filename)
                    urllib.request.urlretrieve(src, filepath)
                    local_url = QUrl.fromLocalFile(filepath).toString()
                    self.saved_media_map[src] = (filename, local_url)
                    display_src = local_url
                    saved_hint = f"<br/><span style='color: #81c995; font-size: 11px;'>[Đã lưu: {filename}]</span>"
                except Exception:
                    pass

            return f'''
            <div class="media-wrapper">
                <img class="generated-media" src="{display_src}" alt="{alt}" title="{alt}"/>
                <div class="media-caption">{alt}{saved_hint}</div>
            </div>
            '''

        # 2. Handle HTML5 Video
        def replace_video(match):
            src = match.group(1)
            saved_hint = ""
            display_src = src
            if src in self.saved_media_map:
                filename, local_url = self.saved_media_map[src]
                display_src = local_url
                saved_hint = f"<br/><span style='color: #81c995; font-size: 11px;'>[Đã lưu video: {filename}]</span>"
            elif src.startswith("data:video/"):
                try:
                    b64_data = src.split(",", 1)[1]
                    filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}.mp4"
                    filepath = os.path.join(MEDIA_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(b64_data))
                    local_url = QUrl.fromLocalFile(filepath).toString()
                    self.saved_media_map[src] = (filename, local_url)
                    display_src = local_url
                    saved_hint = f"<br/><span style='color: #81c995; font-size: 11px;'>[Đã lưu video: {filename}]</span>"
                except Exception:
                    pass
            elif src.startswith("http://") or src.startswith("https://"):
                try:
                    filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}.mp4"
                    filepath = os.path.join(MEDIA_DIR, filename)
                    urllib.request.urlretrieve(src, filepath)
                    local_url = QUrl.fromLocalFile(filepath).toString()
                    self.saved_media_map[src] = (filename, local_url)
                    display_src = local_url
                    saved_hint = f"<br/><span style='color: #81c995; font-size: 11px;'>[Đã lưu video: {filename}]</span>"
                except Exception:
                    pass

            return f'''
            <div class="media-wrapper">
                <video class="generated-video" controls autoplay loop>
                    <source src="{display_src}" type="video/mp4">
                    Trình duyệt không hỗ trợ thẻ video.
                </video>
                <div class="media-caption">Veo AI Video{saved_hint}</div>
            </div>
            '''

        # Replace markdown images
        formatted = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_img, text, flags=re.DOTALL)
        # Replace video tags
        formatted = re.sub(r'<video[^>]*>.*?<source[^>]*src=[\'"](.*?)[\'"][^>]*>.*?</video>', replace_video, formatted, flags=re.DOTALL)

        return formatted

    def send_request(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            return

        url = self.url_input.text().strip()
        key = self.key_input.text().strip()
        model = self.model_input.text().strip()
        is_stream = self.stream_check.isChecked()

        # Render user prompt in WebEngine
        safe_prompt = json.dumps(prompt)
        self.web_view.page().runJavaScript(f"appendUserMessage({safe_prompt});")
        self.prompt_input.clear()

        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText(f"Đang gửi tới {model} qua {url}...")
        self.accumulated_text = ""
        self.saved_media_map = {}

        if is_stream:
            self.web_view.page().runJavaScript("startAiMessage();")

        self.worker = RequestWorker(url, key, model, prompt, is_stream)
        self.worker.chunk_received.connect(self.on_chunk)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    @Slot(str)
    def on_chunk(self, chunk):
        self.accumulated_text += chunk
        html_content = self.format_media_html(self.accumulated_text)
        safe_html = json.dumps(html_content)
        self.web_view.page().runJavaScript(f"updateAiContent({safe_html});")

    @Slot(str, float)
    def on_finished(self, full_text, elapsed):
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText(f"Hoàn thành ({elapsed:.2f}s, {len(full_text)} ký tự). Media đã lưu vào: {MEDIA_DIR}")

        if not self.stream_check.isChecked():
            self.web_view.page().runJavaScript("startAiMessage();")
            html_content = self.format_media_html(full_text)
            safe_html = json.dumps(html_content)
            self.web_view.page().runJavaScript(f"updateAiContent({safe_html});")

        self.web_view.page().runJavaScript("finalizeAiMessage();")

    @Slot(str)
    def on_error(self, err):
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText(f"Lỗi: {err}")
        safe_err = json.dumps(f"<span style='color: #f28b82;'>Lỗi: {err}</span>")
        self.web_view.page().runJavaScript(f"updateAiContent({safe_err});")
        self.web_view.page().runJavaScript("finalizeAiMessage();")

    def stop_request(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.status_label.setText("Đã dừng request bởi người dùng.")
            self.send_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.web_view.page().runJavaScript("finalizeAiMessage();")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    window = ApiTesterWindow()
    window.show()
    sys.exit(app.exec())
