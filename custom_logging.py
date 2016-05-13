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

# try:
#     action_handler = logging.handlers.RotatingFileHandler(
#         config.action_logfile, maxBytes=10485760, backupCount=0)
# except AttributeError:
#     # action_handler = logging.NullHandler()
#     pass


action_handler = logging.handlers.RotatingFileHandler(
    config.action_logfile, maxBytes=10485760, backupCount=0)
action_formatter = logging.Formatter(
    '%(asctime)s: %(message)s')
action_handler.setFormatter(action_formatter)
action_handler.setLevel(logging.INFO)


def get_logger(name):
    log = logging.getLogger(name)
    log.setLevel(level)
    log.addHandler(handler)
    return log


def get_action_logger():
    log = logging.getLogger('_action_logger')
    log.setLevel(logging.INFO)
    log.addHandler(action_handler)
    return log
