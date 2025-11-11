import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "users.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("DELETE FROM users;")
conn.commit()
conn.close()

print("All users deleted.")