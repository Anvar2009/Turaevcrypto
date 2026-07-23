import sqlite3

def init_db():
    conn = sqlite3.connect("taz_bot.db")
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        taz_balance REAL DEFAULT 0,
        usdt_balance REAL DEFAULT 0,
        ton_balance REAL DEFAULT 0,
        btc_balance REAL DEFAULT 0,
        eth_balance REAL DEFAULT 0
    )
    """)

    # Vazifalar jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        link TEXT,
        reward_taz REAL
    )
    """)

    # Bajarilgan vazifalar jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_tasks (
        user_id INTEGER,
        task_id INTEGER
    )
    """)

    # Valyuta kurslari jadvali (1 TAZ = X crypto)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rates (
        crypto TEXT PRIMARY KEY,
        rate REAL
    )
    """)
    
    # Boshlang'ich kurslar
    cursor.execute("INSERT OR IGNORE INTO rates VALUES ('USDT', 0.1), ('TON', 0.02), ('BTC', 0.000001), ('ETH', 0.00003)")

    conn.commit()
    conn.close()

init_db()
