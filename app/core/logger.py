import logging

from app.config import ROOT_PATH


def get_logger(name="app") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        create_logger(name)

    return logger


def create_logger(name="app", log_level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s")

        logging.basicConfig(level=log_level)
        logfile = ROOT_PATH / "logs" / f"{name}.log"
        if not logfile.parent.exists():
            logfile.parent.mkdir(parents=True, exist_ok=True)
        if not logfile.exists():
            logfile.touch()
        fh = logging.FileHandler(logfile, encoding="utf-8")

        fh.setLevel(log_level)
        logger.setLevel(log_level)

        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
