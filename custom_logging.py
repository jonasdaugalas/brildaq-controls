import logging
import logging.handlers
import config


level = logging.getLevelName(config.loglevel)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]: %(message)s')
handler = logging.handlers.RotatingFileHandler(
    config.logfile, maxBytes=10485760, backupCount=5)
handler.setLevel(level)
handler.setFormatter(formatter)


def get_logger(name):
    log = logging.getLogger(name)
    log.setLevel(level)
    log.addHandler(handler)
    return log
