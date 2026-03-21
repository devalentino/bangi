import logging.config
import sys

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '%(levelname)s %(asctime)s %(pathname)s %(lineno)s %(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        },
    },
    'handlers': {
        'json_to_console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'stream': sys.stdout,
        },
    },
    'loggers': {
        'root': {
            'handlers': ['json_to_console'],
            'propagate': True,
            'level': 'INFO',
        }
    },
}


def configure_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
