import os
import glob
import sqlite3
import shutil

user_data = r"C:\Users\vutru\AppData\Local\Google\Chrome\User Data"
for db in glob.glob(os.path.join(user_data, "*", "Network", "Cookies")):
    prof = db.split(os.sep)[-3]
    tmp = r"H:\reqble-mcp\chatgpt-revert\tmp_check.db"
    try:
        shutil.copyfile(db, tmp)
        conn = sqlite3.connect(tmp)
        c = conn.cursor()
        c.execute("SELECT count(*) FROM cookies WHERE host_key LIKE '%chatgpt%'")
        cnt = c.fetchone()[0]
        conn.close()
        os.remove(tmp)
        if cnt > 0:
            print(f"Profile '{prof}' has {cnt} chatgpt cookies!")
    except Exception as e:
        print(f"Error on {prof}: {e}")
