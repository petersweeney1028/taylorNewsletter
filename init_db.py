from app import app, db  # Import app and db from your main Flask application file

def init_db():
    """ Initialize the database. """
    with app.app_context():
        # Create tables
        db.create_all()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
