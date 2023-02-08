from loguru import logger


logger_config = {
    "handlers": [
        {
            "sink": "logs/bot.log",
            "format": "{time:YYYY-MM-DD at HH:mm:ss Z} | {level} | {message}",
            "encoding": "utf-8",
            "level": "DEBUG",
            "rotation": "10 MB",
            "compression": "zip"
        },
    ],
}

logger.configure(**logger_config)