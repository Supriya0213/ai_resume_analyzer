import sqlite3

def create_database():
    connection = sqlite3.connect("resumes.db")
    cursor = connection.cursor()

    with open("schema.sql", "r") as f:
        schema = f.read()

    cursor.executescript(schema)
    connection.commit()
    connection.close()
    print("Database created successfully!")

create_database()
