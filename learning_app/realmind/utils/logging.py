import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logging(app):
    """
    Attach a rotating file handler to the app logger. If the log directory
    or file isn't writable, fall back to stderr only — never crash the app
    over a logging configuration issue.
    """
    log_dir = os.path.join(app.root_path, 'logs')

    try:
        os.makedirs(log_dir, exist_ok=True)
        handler = RotatingFileHandler(
            os.path.join(log_dir, 'fliers.log'),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s] %(message)s'
        ))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("File logging enabled.")
    except (OSError, PermissionError) as e:
        # Don't take the whole site down over a log file permission glitch.
        # Stderr will still be captured by systemd journalctl.
        app.logger.warning(f"File logging disabled: {e}")