"""Модуль логирования
"""
import logging
from logging.handlers import TimedRotatingFileHandler
from utils.config import config


def init_logger():
    """Инициализация логирования"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    FORMATTER_TEMPLATE = "%(asctime)s - [%(levelname)s] - %(name)s"\
        " - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s\n{}"
    console_formatter = logging.Formatter(FORMATTER_TEMPLATE.format('_'*13))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if config['GENERAL'].get('MODE') == 'PROD':
        file_handler = TimedRotatingFileHandler(
            filename='logs/.log',
            when='d',
            interval=1,
            backupCount=5
        )
        file_handler.setFormatter(console_formatter)
        file_handler.setLevel(level=logging.INFO)
        logger.addHandler(file_handler)
    return logger


log = init_logger()
