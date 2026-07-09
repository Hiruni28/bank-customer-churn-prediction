import sqlite3


def init_db():

    conn = sqlite3.connect("bank.db")

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_name TEXT,

        user_email TEXT,

        probability REAL,

        prediction TEXT,

        risk_level TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()

    conn.close()