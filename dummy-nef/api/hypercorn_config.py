log_format = '%(asctime)s: [%(name)s] %(levelname)s: [%(module)s] %(message)s [%(process)d] (%(filename)s:%(lineno)d)'

# Define the log configuration dictionary
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": log_format,
            "datefmt": "%m/%d %H:%M:%S.%f",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console"],
    },
    "loggers": {
        "hypercorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}