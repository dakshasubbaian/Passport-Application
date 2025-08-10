import cx_Oracle

# Setup DSN (replace if your Oracle details differ)
dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE")

# Connect (replace user and password with your Oracle credentials)
conn = cx_Oracle.connect(user="system", password="daksha", dsn=dsn)

cursor = conn.cursor()
cursor.execute("SELECT sysdate FROM dual")
result = cursor.fetchone()
print("Oracle current date/time:", result[0])

conn.close()
