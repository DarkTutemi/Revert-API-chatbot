# DeepSeek Web Reverse Proxy Gateway (`deepseek-revert`)

> **Port:** 3002  
> **Target Domain:** https://chat.deepseek.com/  
> **API Format:** OpenAI-Compatible (`/v1/chat/completions`, `/v1/models`)  

---

## 1. Tính Năng Nổi Bật

- **Zero Ban & Zero 403:** Hoạt động trực tiếp trên phiên đăng nhập của Chrome thông qua Extension Bridge.
- **Hỗ trợ DeepSeek-R1 Thinking:** Tự động bắt chuỗi tư duy của R1 (`type: "thinking"`) và bọc trong cặp tag `<think>...</think>` chuẩn xác.
- **Tự động chuyển Model:** Tự động bật nút "DeepThink (R1)" khi chọn model `deepseek-reasoner` / `deepseek-r1`, và tự động tắt khi chọn `deepseek-chat` / `deepseek-v3`.
- **Cơ chế Dual-Capture:**
  1. **Fetch Hook (Chính):** Bắt trực tiếp luồng stream `/api/v0/chat/completion` với độ trễ 0ms.
  2. **DOM Observer (Dự phòng):** Tự động đọc nội dung nếu API stream bị mã hóa hoặc thay đổi cấu trúc.

---

## 2. Hướng Dẫn Cài Đặt Extension

1. Mở Chrome trên profile đã đăng nhập https://chat.deepseek.com/.
2. Truy cập `chrome://extensions`.
3. Bật **Developer mode** (Chế độ dành cho nhà phát triển).
4. Bấm **Load unpacked** (Tải tiện ích đã giải nén).
5. Chọn thư mục:
   ```
   H:\reqble-mcp\deepseek-revert\extension
   ```
6. Mở hoặc F5 lại tab `https://chat.deepseek.com/`.

---

## 3. Thử Nghiệm API

### Cách 1: Qua PySide6 Tester GUI
- Mở file `H:\reqble-mcp\gui_tester.py` (hoặc chạy `H:\reqble-mcp\start_gui_tester.bat`).
- Tại ô **Cổng**, chọn **DeepSeek Gateway (Port 3002)**.
- Gửi prompt và nhận câu trả lời kèm quá trình suy nghĩ `<think>`.

### Cách 2: Qua cURL / Python
```bash
python scripts/test_deepseek.py
```
