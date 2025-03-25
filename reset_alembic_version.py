# reset_alembic_version.py
from app import app, db
from alembic.migration import MigrationContext
from alembic.operations import Operations

with app.app_context():
    conn = db.engine.connect()
    context = MigrationContext.configure(conn)
    op = Operations(context)

    # Replace with the correct version you want to set
    op.execute("UPDATE alembic_version SET version_num = 'a6ea6a5a759b'")
    print("Alembic version updated manually.")
