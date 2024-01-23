import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('/Users/petersweeney/Desktop/Coding/taylorNewsletter/newsletter.db')

# Create a cursor object
cursor = conn.cursor()

# SQL query to select all emails from the subscribers table
query = "SELECT email FROM subscribers"

# Execute the query
cursor.execute(query)

# Fetch all rows (all emails) from the database
emails = cursor.fetchall()

# Execute a query to count the number of records in the subscribers table
cursor.execute('SELECT COUNT(*) FROM subscribers')

# Fetch the result
count = cursor.fetchone()[0]

# Close the cursor and connection
cursor.close()
conn.close()

# Print the emails
for email in emails:
    print(email[0])

if count == 0:
    print("The subscribers table is empty.")
else:
    print(f"The subscribers table has {count} records.")