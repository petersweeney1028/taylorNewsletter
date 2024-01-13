import sqlite3

# Create a new SQLite database (or connect if it already exists)
conn = sqlite3.connect('/Users/petersweeney/Desktop/Coding/taylorNewsletter/backup/newsletter.db')

# Create a new table named 'subscribers'
conn.execute('''CREATE TABLE subscribers (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL
                )''')

# Commit changes and close the connection
conn.commit()
conn.close()

