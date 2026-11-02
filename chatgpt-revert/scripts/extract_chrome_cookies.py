import os
import sys
import json
import base64
import sqlite3
import shutil
import win32crypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

sys.stdout.reconfigure(encoding='utf-8')

user_data = r"C:\Users\vutru\AppData\Local\Google\Chrome\User Data"
local_state_path = os.path.join(user_data, "Local State")

# 1. Get encryption key
with open(local_state_path, "r", encoding="utf-8") as f:
    local_state = json.load(f)

encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
# Remove 'DPAPI' prefix (first 5 bytes)
encrypted_key = encrypted_key[5:]
key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

# 2. Copy cookies DB to temp location (avoid lock)
cookies_src = os.path.join(user_data, "Profile 16", "Network", "Cookies")
cookies_copy = r"H:\reqble-mcp\chatgpt-revert\cookies_temp.db"
shutil.copyfile(cookies_src, cookies_copy)

# 3. Query cookies for chatgpt.com
conn = sqlite3.connect(cookies_copy)
cursor = conn.cursor()
cursor.execute("SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%chatgpt.com%'")

decrypted_cookies = {}
for name, enc_val in cursor.fetchall():
    try:
        # Check v10 prefix (Chrome AES-GCM)
        if enc_val[:3] == b'v10':
            nonce = enc_val[3:15]
            ciphertext = enc_val[15:]
            aesgcm = AESGCM(key)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8', errors='replace')
            decrypted_cookies[name] = decrypted
    except Exception as e:
        pass

conn.close()
os.remove(cookies_copy)

print(f"Decrypted {len(decrypted_cookies)} cookies for chatgpt.com:")
for k in decrypted_cookies:
    val = decrypted_cookies[k]
    print(f"- {k}: {val[:30]}... ({len(val)} chars)")

# Save full cookie string
cookie_str = "; ".join([f"{k}={v}" for k, v in decrypted_cookies.items()])
with open(r"H:\reqble-mcp\chatgpt-revert\fresh_cookies.txt", "w", encoding="utf-8") as f:
    f.write(cookie_str)
print("Saved fresh cookies to H:/reqble-mcp/chatgpt-revert/fresh_cookies.txt")
