import sqlite3


conn = sqlite3.connect('date.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE chat_data (
    id                INTEGER PRIMARY KEY    AUTOINCREMENT,
    chat_id           INT     NOT NULL,
    message_ts        INT,
    message           CHAR(500)
);''')