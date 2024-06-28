import logging
import sys
from pathlib import Path

from concurrent_log_handler import ConcurrentRotatingFileHandler


def config_script_logger(name: str, filename: str, level=logging.INFO, stdout: bool = False):
    log_dir = Path('/var/log/evcloud')
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    filename = log_dir.joinpath(filename)
    return config_logger(name=name, filename=filename, level=level, stdout=stdout)


def config_logger(name: str, filename: Path, level=logging.INFO, stdout: bool = False):
    logger = logging.Logger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(message)s ",  # 配置输出日志格式
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    if stdout:
        std_handler = logging.StreamHandler(stream=sys.stdout)
        std_handler.setFormatter(formatter)
        logger.addHandler(std_handler)

    file_handler = ConcurrentRotatingFileHandler(
        filename=filename, maxBytes=1024*1024*20, backupCount=5, use_gzip=True)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.WARNING)
    logger.addHandler(file_handler)
    return logger
