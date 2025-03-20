import logging
import logging.config


server_logger = logging.getLogger('crypto_converter')


def init_logging():
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }

    logging.config.dictConfig(logging_config)
