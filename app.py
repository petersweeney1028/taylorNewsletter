import os
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError 

app = Flask(__name__, template_folder=os.getcwd())
CORS(app, origins=["https://www.taylortimes.news", "http://127.0.0.1:5000/"])


uri = os.getenv('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'sqlite:///newsletter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

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
        new_subscriber = Subscriber(email=email)
        db.session.add(new_subscriber)
        db.session.commit()

        if send_welcome_email(email):
            return jsonify({"success": True, "message": "Subscription successful. Please check your email."})
        else:
            return jsonify({"success": False, "message": "Subscription successful but failed to send email."})
    except Exception as e:
        db.session.rollback()  # Rollback in case of any error
        if isinstance(e, sqlalchemy.exc.IntegrityError):
            return jsonify({"success": False, "message": "Email already subscribed"})
        print(f"Database or email error: {e}")
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)