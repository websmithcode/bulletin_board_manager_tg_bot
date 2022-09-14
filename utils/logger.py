import logging

log = logging.getLogger()
log.setLevel(logging.DEBUG)


c_handler = logging.StreamHandler()

c_formatter = logging.Formatter(
    "%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s")

c_handler.setFormatter(c_formatter)
log.addHandler(c_handler)
