import logging
import time

logging.captureWarnings(True)
logging.TRACE = 9
logging.addLevelName(logging.TRACE, "TRACE")


def trace(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    self._log(logging.TRACE, message, args, **kws)


logging.Logger.trace = trace


def get_log_stream_handler(log_level):
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(LogFormatter())
    return ch


def get_log_file_handler(log_level, file):
    fh = logging.FileHandler(file)
    fh.setLevel(log_level)
    fh.setFormatter(LogFormatter(True))
    return fh


def configure_logger_by_name(logger_name, console_level, file_level, file_path):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.TRACE)
    logger.handlers.clear()
    logger.propagate = False

    logger.addHandler(get_log_stream_handler(console_level))
    logger.setLevel(logging.TRACE)
    logger.addHandler(get_log_file_handler(file_level, file_path))


def configure_logger(log_config):
    configure_logger_by_name(
        "extractor",
        log_config.get("main").get("console_level"),
        log_config.get("main").get("file_level"),
        log_config.get("main").get("file_path"),
    )

    for module_type in ["external_modules", "internal_modules"]:
        for module_name in log_config.get(module_type):
            configure_logger_by_name(
                module_name,
                log_config.get(module_type).get(module_name).get("console_level")
                or log_config.get("main").get("console_level"),
                log_config.get(module_type).get(module_name).get("file_level")
                or log_config.get("main").get("file_level"),
                log_config.get(module_type).get(module_name).get("file_path")
                or log_config.get("main").get("file_path"),
            )

    return


def get_elapsed_time_message(task, start_time, end_time=None):
    if end_time is None:
        end_time = time.time()
    return (
        "Elapsed time (" + task + "): " + str(round(end_time - start_time)) + " seconds"
    )


class LogFormatter(logging.Formatter):
    def __init__(self, is_file=False):
        super().__init__()

        self.is_file = is_file

        self.reset = "\033[0m"
        self.format_str1 = "%(asctime)s | %(levelname)-8s | %(name)-20s | "
        self.format_str2 = "%(message)s (%(filename)s:%(lineno)d)"
        self.format_date = "%d-%m %H:%M:%S"

        self.colors = {
            logging.TRACE: "\033[94m",
            logging.DEBUG: "\033[35m",
            logging.INFO: "\033[94m",
            logging.WARNING: "\033[31;21m",
            logging.ERROR: "\033[38;5;196m",
            logging.CRITICAL: "\033[31;1m",
        }

    def format(self, record):

        if self.is_file:
            return logging.Formatter(
                self.format_str1 + self.format_str2, self.format_date
            ).format(record)

        log_fmt = (
            self.colors.get(record.levelno)
            + self.format_str1
            + self.format_str2
            + self.reset
        )
        formatter = logging.Formatter(log_fmt, self.format_date)
        return formatter.format(record)
