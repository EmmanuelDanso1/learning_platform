import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    log_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    handler = RotatingFileHandler(
        os.path.join(log_dir, 'fliers.log'),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5
    )

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    # Prevent duplicate handlers (important for reloads / gunicorn)
    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        app.logger.addHandler(handler)

    app.logger.setLevel(logging.INFO)
