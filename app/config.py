import configparser
from pathlib import Path
from typing import Union

CONFIG = {}
ROOT_PATH = Path(__file__).parent.parent.resolve()
LOG_PATH = ROOT_PATH / 'logs'
APP_PATH = ROOT_PATH / 'app'
PUBLIC_PATH = ROOT_PATH / 'public'


def get_config(path: str, default=None) -> Union[str, dict, list, int, float, bool, None]:
    global CONFIG
    if not CONFIG:
        load_config()

    value = CONFIG
    pieces = path.split(".")
    for field in pieces:
        if field not in value:
            return default

        value = value[field]

    return value


def load_config():
    global CONFIG

    if not CONFIG:
        parser = configparser.ConfigParser()
        parser.read(ROOT_PATH / 'config.ini')

        for section in parser.sections():
            CONFIG[section] = {}

            for key, value in parser.items(section):
                CONFIG[section][key] = value
