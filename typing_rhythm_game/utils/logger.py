import logging
import os
from logging.handlers import RotatingFileHandler
from flask import has_request_context, request

class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.method = request.method
            if hasattr(request, 'user_id'):
                record.user_id = request.user_id
            else:
                record.user_id = 'anonymous'
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
            record.user_id = None

        return super().format(record)

def setup_logger(app):
    if not os.path.exists('logs'):
        os.mkdir('logs')

    formatter = RequestFormatter(
        '[%(asctime)s] %(remote_addr)s - User:%(user_id)s '
        '%(levelname)s in %(module)s: %(message)s '
        'URL: %(url)s - Method: %(method)s'
    )

    file_handler = RotatingFileHandler(
        'logs/typing_game.log', 
        maxBytes=10240000,
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Typing Game startup')
