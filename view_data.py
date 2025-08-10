import sqlite3

DB_NAME = 'passport.db'

def fetch_all_records():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications")
    rows = cursor.fetchall()
    conn.close()

    print("All Passport Applications:\n")
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"First Name: {row[1]}")
        print(f"Last Name: {row[2]}")
        print(f"DOB: {row[3]}")
        print(f"Gender: {row[4]}")
        print(f"Email: {row[5]}")
        print(f"Phone: {row[6]}")
        print(f"Address: {row[7]}")
        print("-" * 40)

if __name__ == "__main__":
    fetch_all_records()
