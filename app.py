import os
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__, template_folder=os.getcwd())
CORS(app, origins=["https://www.taylortimes.news", "http://127.0.0.1:5000/"])


def init_db():
    conn = sqlite3.connect('newsletter.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

# Call init_db to initialize the database
init_db()

def send_welcome_email(email):
    try:
        sg_api_key = os.getenv('SENDGRID_API_KEY')
        if not sg_api_key:
            raise ValueError("SendGrid API key not found in environment variables.")
        sg = SendGridAPIClient(sg_api_key)
        from_email = 'swiftie@taylortimes.news'
        subject = 'Welcome to Taylor Times!'
        content = '<p>Thank you for subscribing to Taylor Times! Stay tuned for updates.</p>'
        message = Mail(from_email=from_email, to_emails=email, subject=subject, html_content=content)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']
    try:
        with sqlite3.connect('/Users/petersweeney/Desktop/Coding/taylorNewsletter/newsletter.db') as conn:
            conn.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
            conn.commit()
        if send_welcome_email(email):
            return jsonify({"success": True, "message": "Subscription successful. Please check your email."})
        else:
            return jsonify({"success": False, "message": "Subscription successful but failed to send email."})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Email already subscribed"})
    except Exception as e:
        print(f"Database or email error: {e}")
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)