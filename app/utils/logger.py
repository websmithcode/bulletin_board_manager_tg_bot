"""Модуль логирования
"""
import logging
from logging.handlers import TimedRotatingFileHandler
from utils.config import config

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

FORMATTER_TEMPLATE = "%(asctime)s - [%(levelname)s] - %(name)s"\
    " - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s\n{}"
console_formatter = logging.Formatter(FORMATTER_TEMPLATE.format('_'*13))

console_handler = logging.StreamHandler()
console_handler.setFormatter(console_formatter)
log.addHandler(console_handler)

if config['GENERAL'].get('MODE') == 'PROD':
    file_handler = TimedRotatingFileHandler(
        filename='logs/.log',
        when='d',
        interval=1,
        backupCount=5
    )
    file_handler.setFormatter(console_formatter)
    file_handler.setLevel(level=logging.INFO)
    log.addHandler(file_handler)
