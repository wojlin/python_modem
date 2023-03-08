from dataclasses import dataclass
import logging
import json
import sys
import os

def setup_config():
    user_id = input("user id: ")
    modulation_type = input("modulation type: ")
    verbose = True if input("verbose y/N: ") == "y" else False

    dir_name = '/'.join(os.path.dirname(os.path.realpath(__file__)).split('/')[:-1])
    path = f"{dir_name}/configs/peer_to_peer_config.json"
    with open(path) as f:
        peer_config = json.loads(f.read())

    return Config(user_id=user_id, modulation_type=modulation_type, verbose=verbose, peer_config=peer_config)

def setup_audio_devices(devices: dict):
    print("INPUT DEVICES:")
    for _, device in devices["input"].items():
        print(f"{device['index']}. {device['name']}")
    selected_input = input("select input device: ")
    print()
    print("OUTPUT DEVICES:")
    for _, device in devices["output"].items():
        print(f"{device['index']}. {device['name']}")
    print()
    selected_output = input("select output device: ")
    return int(devices["input"][selected_input]["device_index"]), int(devices["output"][selected_output]["device_index"])

@dataclass
class Config:
    user_id: str
    modulation_type: str
    verbose: bool
    peer_config: dict

class __CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s %(msecs)03dms - (%(filename)s:%(lineno)d) - %(levelname)s - %(message)s "

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def configure_logging(logs_path, logs_name) -> logging.Logger:
    """
    this method configures logging
    :param args: dict of parsed args from parse_args method
    :return:
    """
    log_path = logs_path
    level = logging.ERROR

    fileh = logging.FileHandler(log_path, 'w')
    formatter = logging.Formatter('%(asctime)s %(msecs)03dms - (%(filename)s:%(lineno)d) - %(levelname)s - %(message)s ')
    fileh.setFormatter(formatter)

    logger = logging.getLogger(logs_name)

    for hdlr in logger.handlers[:]:  # remove all old handlers
        logger.removeHandler(hdlr)
    logger.addHandler(fileh)

    logger.setLevel(level)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(__CustomFormatter())
    logger.addHandler(ch)

    return logger