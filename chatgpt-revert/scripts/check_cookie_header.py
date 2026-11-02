import sqlite3
import shutil
import os

tmp = r"H:\reqble-mcp\chatgpt-revert\tmp_check.db"
shutil.copyfile(r"C:\Users\vutru\AppData\Local\Google\Chrome\User Data\Profile 16\Network\Cookies", tmp)
conn = sqlite3.connect(tmp)
c = conn.cursor()
c.execute("SELECT name, hex(substr(encrypted_value, 1, 4)) FROM cookies WHERE host_key LIKE '%chatgpt%' LIMIT 5")
for r in c.fetchall():
    print(r)
conn.close()
os.remove(tmp)
