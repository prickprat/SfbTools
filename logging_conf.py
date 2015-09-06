# Configuration File for logging in Skype for Business Tools

# Specify the logging level here
LOGGING_LEVEL = 'DEBUG'

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
