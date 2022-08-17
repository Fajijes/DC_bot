'''
Date: 2020-12-22 10:43:43
LastEditors: Rustle Karl
LastEditTime: 2021-03-12 12:20:11
'''
import logging
import os
from logging import DEBUG, ERROR, Formatter, INFO, Logger, LogRecord, WARNING
from logging.handlers import RotatingFileHandler

from pkgs.color import Color, sbluef, set_color, unset_color

_color_config = {
    'DEBUG': Color.Cyan,
    'INFO': Color.Green,
    'WARNING': Color.Yellow,
    'ERROR': Color.Red,
}


class LogFormatter(Formatter):

    def __init__(self, fmt, datefmt=None, config=None) -> None:
        super(LogFormatter, self).__init__(fmt, datefmt)
        self.config = config if config else _color_config

    def parse_color(self, level):
        return set_color(self.config.get(level, Color.Green))

    def format(self, record: LogRecord) -> str:
        record.color = self.parse_color(record.levelname)
        record.pathname = record.pathname.replace("\\", "/")
        return unset_color(super(LogFormatter, self).format(record))


levels = {
    "debug": DEBUG,
    "info": INFO,
    "warn": WARNING,
    "warning": WARNING,
    "error": ERROR,
}


def convert_level(level: str):
    return levels.get(level, INFO)


_logger_config = {
    'mode': 'w',
    'encoding': 'utf-8',
    'maxBytes': (1 << 20) * 50,  # MB
    'backupCount': 30,
}

_logfile_format = "%(asctime)s %(levelname)s %(pathname)s:%(lineno)s %(message)s"
_stdout_format = "> {}\n> %(asctime)s %(color)s[%(levelname)s] %(message)s\n". \
    format(sbluef("%(pathname)s:%(lineno)s"))


def get_logger(ns: str, level: str = "debug", logfile: str = '', ext='.log',
               logdir='logs', stdout=True, **kwargs) -> Logger:
    level = convert_level(level)

    logger = logging.getLogger(ns)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # 日志文件
    if logfile:
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        if not logfile.endswith(ext):
            logfile += ext

        logfile = os.path.join(logdir, logfile)
        file_handler = RotatingFileHandler(
                logfile,
                mode=kwargs.get('mode', _logger_config['mode']),
                encoding=kwargs.get('encoding', _logger_config['encoding']),
                maxBytes=kwargs.get('maxBytes', _logger_config['maxBytes']),
                backupCount=kwargs.get(
                        'backupCount', _logger_config['backupCount']),
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(Formatter(_logfile_format))  # 为文件输出设定格式
        logger.addHandler(file_handler)

    # 控制台
    if stdout or not logfile:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(LogFormatter(_stdout_format))  # 控制台输出设定格式
        logger.addHandler(console_handler)

    return logger


log = get_logger('unknown')

debug = log.debug
info = log.info
warning = log.warning
error = log.error

if __name__ == "__main__":
    debug("I don't know")
    info("I don't know")
    warning("I don't know")
    error("I don't know")
