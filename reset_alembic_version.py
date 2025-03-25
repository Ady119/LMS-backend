from app import app, db 
from alembic.migration import MigrationContext
from alembic.operations import Operations

with app.app_context():
    connection = db.engine.connect()
    context = MigrationContext.configure(connection)
    op = Operations(context)

    op._proxy.execute("UPDATE alembic_version SET version_num = 'a6ea6a5a759b'")
    print(" Alembic version reset to a6ea6a5a759b.")
