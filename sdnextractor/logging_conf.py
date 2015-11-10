# Configuration File for logging in Skype for Business Tools

# Specify the logging level here {CRITICAL, ERROR, WARN, INFO, DEBUG} }
LOGGING_LEVEL = 'INFO'

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "%(asctime)s [%(name)s :: %(levelname)s] " +
                        "[%(module)s :: %(funcName)s] " +
                        ">>> %(message)s"
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOGGING_LEVEL,
        'propagate': False
    }
}
