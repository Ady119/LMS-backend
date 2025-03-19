from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import app, db  # Import your Flask app and db

# Initialize manager with the Flask app
manager = Manager(app)

# Initialize Migrate with the Flask app and SQLAlchemy db
migrate = Migrate(app, db)

# Add the 'db' command to manage database migrations
manager.add_command('db', MigrateCommand)

if __name__ == "__main__":
    manager.run()
