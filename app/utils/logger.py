import logging
from flask import current_app

def setup_logging(app):
    """
    Sets up logging for the Flask application.
    """
    if not app.debug:
        # In production, log to a file
        logging.basicConfig(filename='jobalizer.log',
                            level=logging.INFO,
                            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    else:
        # In development, log to the console
        logging.basicConfig(level=logging.DEBUG)
