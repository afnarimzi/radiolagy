
import sqlite3
import os

DB_PATH = "c:\\MM_internship\\radilolagy\\MM-DUK-Interns\\radiology_ai.db"

def check_sqlite():
    if not os.path.exists(DB_PATH):
        print(f"File not found: {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        print("--- Recent Inputs in SQLite ---")
        cursor.execute("SELECT case_id, created_at FROM patient_inputs ORDER BY created_at DESC LIMIT 5")
        for row in cursor.fetchall():
            print(f"CASE_ID: {row[0]} | CREATED: {row[1]}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    check_sqlite()
