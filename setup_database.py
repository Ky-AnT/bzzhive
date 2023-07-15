import sqlite3

# Create a connection to the SQLite database
conn = sqlite3.connect('database.db')

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Create the 'users' table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')

# Create the 'notes' table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        content TEXT,
        shared INTEGER DEFAULT 0,
        shared_with TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS shared_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER,
        shared_with TEXT,
        FOREIGN KEY (note_id) REFERENCES notes (id),
        FOREIGN KEY (shared_with) REFERENCES users (username)
    )
''')


# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database and tables created successfully.")
