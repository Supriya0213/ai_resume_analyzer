import sqlite3

connection = sqlite3.connect("resumes.db")
cursor = connection.cursor()
cursor.execute("SELECT * FROM EDUCATION")
for row in cursor.fetchall():
    print(row)
connection.close()