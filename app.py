import os
from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
import sqlite3


app = Flask(__name__, template_folder=os.getcwd())  # Set the current working directory as the template folder

# Initialize and connect to SQLite database
class DatabaseConnection:
    def __enter__(self):
        self.conn = sqlite3.connect('newsletter.db')
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

def get_db_connection():
    return DatabaseConnection()

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route for handling subscriptions
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']
    try:
        with get_db_connection() as conn:
            conn.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
            conn.commit()
        return jsonify({"success": True, "message": "Subscription successful"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Email already subscribed"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
