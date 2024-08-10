import sqlite3
import logging
import click
from flask import current_app, g

def get_db_connection():
    """
    Establish a connection to the SQLite database.
    Returns a connection object with row factory set to access columns by name.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row  # Access columns by name
    return g.db

def close_db(e=None):
    """
    Close the database connection if it exists.
    """
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    """
    Initialize the database using schema.sql file.
    """
    with current_app.app_context():
        db = get_db_connection()
        try:
            # Check if the table exists
            table_exists = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='job_postings';").fetchone()
            if not table_exists:
                with current_app.open_resource('schema.sql', mode='r') as f:
                    db.cursor().executescript(f.read())
                db.commit()
        except Exception as e:
            logging.error(f"Error initializing the database: {e}")
        finally:
            db.close()

@click.command('init-db')
def init_db_command():
    """
    CLI command to initialize the database.
    """
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    """
    Register database functions with the Flask app.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)