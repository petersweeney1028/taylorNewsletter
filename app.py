import os
from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
import sqlite3
from sendgrid import SendGridAPIClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


app = Flask(__name__, template_folder=os.getcwd())  # Set the current working directory as the template folder
CORS(app, resources={r"/subscribe": {"origins": ["https://www.taylortimes.news"]}})

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

def send_welcome_email(email):
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        from_email = 'swiftie@taylortimes.news'
        subject = 'Welcome to Taylor Times!'
        content = '<p>Thank you for subscribing to Taylor Times! Stay tuned for updates.</p>'
        message = Mail(from_email=from_email, to_emails=email, subject=subject, html_content=content)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route for handling subscriptions
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']
    try:
        with sqlite3.connect('newsletter.db') as conn:
            conn.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
            conn.commit()
        if send_welcome_email(email):
            return jsonify({"success": True, "message": "Subscription successful. Please check your email."})
        else:
            return jsonify({"success": False, "message": "Subscription successful but failed to send email."})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Email already subscribed"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)