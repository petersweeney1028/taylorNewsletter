from flask import Flask, render_template, request, jsonify, url_for
import sqlite3

app = Flask(__name__)

# Initialize and connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect('/Users/petersweeney/Desktop/Coding/taylorNewsletter/backup/newsletter.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route for the main page
@app.route('/')
def index():
    return render_template('taylorLanding.html')

# Route for handling subscriptions
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']
    conn = get_db_connection()
    conn.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Subscription successful"})

if __name__ == '__main__':
    app.run(debug=True)
