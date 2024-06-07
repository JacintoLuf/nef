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
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "hypercorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "pymongo": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        },
        "httpx": {
            "level": "WARNING",  # Set log level to WARNING to suppress INFO and DEBUG logs
            "handlers": ["console"],
            "propagate": False,
        },
    },
}