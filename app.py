import os
from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
import sqlite3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import SENDGRID_API_KEY
client = SendGridAPIClient(api_key=SENDGRID_API_KEY)


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
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    from_email = 'swiftie@taylortimes.news'  # Replace with your new email address
    subject = 'Welcome to Taylor Times! Please Confirm Your Email'
    content = '''
        <p>Thank you for subscribing to Taylor Times! Please reply to this email to make sure you get our next edition.</p>
    '''
    message = Mail(
        from_email=from_email,
        to_emails=email,
        subject=subject,
        html_content=content
    )
    sg.send(message)

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route for handling subscriptions
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']

    # Insert the new subscriber into the database with 'confirmed' defaulting to FALSE
    try:
        with sqlite3.connect('newsletter.db') as conn:
            conn.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
            conn.commit()

        # Send a welcome email to the new subscriber
        send_welcome_email(email)

        return jsonify({"success": True, "message": "Subscription initiated. Please check your email to confirm."})
    except sqlite3.IntegrityError:
        # This block is executed if the email is already in the database
        return jsonify({"success": False, "message": "Email already subscribed"})
    except Exception as e:
        # Handle other exceptions
        return jsonify({"success": False, "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
