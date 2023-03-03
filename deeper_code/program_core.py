from typing import Sequence, Optional
from dataclasses import dataclass
import numpy as np
from glob import glob
import argparse
import logging
import inspect
import wave
import sys
import os

from deeper_code.interfaces import Modulator, Demodulator
from deeper_code.utils import Binary, Audio


@dataclass
class core_data:
    logger: logging.Logger
    modulators: dict
    demodulators: dict
    args: dict
    data: Binary


class program_core:
    def __init__(self, argv):
        self.__modulators = self.__load_package(Modulator)
        self.__demodulators = self.__load_package(Demodulator)
        self.__args = self.__parse_args(argv, self.__modulators, self.__demodulators)
        self.__logger = self.__configure_logging(self.__args)

        self.__logger.info(f"received app run args: {self.__args}")
        self.__logger.info(f"loaded modulators: {', '.join([mod for mod, cls in self.__modulators.items()])}")
        self.__logger.info(f"loaded demodulators: {', '.join([mod for mod, cls in self.__demodulators.items()])}")

        if self.__args["command"] == "modulate":
            self.__data = self.__load_data_to_bytearray(self.__args["input"])
        elif self.__args["command"] == "demodulate":
            self.__data = self.__decode_samples_from_file(self.__args["input"])
        else:
            raise TypeError(f"program can be run either in modulate or demodulate mode! '{self.__args['command']}' is not valid")

    def getData(self):
        return core_data(self.__logger, self.__modulators, self.__demodulators, self.__args, self.__data)

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

    def __configure_logging(self, args: dict) -> logging.Logger:
        """
        this method configures logging
        :param args: dict of parsed args from parse_args method
        :return:
        """
        log_path = "../log.txt"
        level = logging.DEBUG if args["verbose"] else logging.INFO
        level = logging.CRITICAL if args["raw"] else level

        """logging.basicConfig(filename=log_path,
                            filemode="w",
                            format="%(asctime)s %(msecs)03dms - (%(filename)s:%(lineno)d) - %(levelname)s - %(message)s ",
                            level=level)
        logging.info("python modem")"""

        fileh = logging.FileHandler(log_path, 'w')
        formatter = logging.Formatter('%(asctime)s %(msecs)03dms - (%(filename)s:%(lineno)d) - %(levelname)s - %(message)s ')
        fileh.setFormatter(formatter)

        logger = logging.getLogger("python_modem")

        for hdlr in logger.handlers[:]:  # remove all old handlers
            logger.removeHandler(hdlr)
        logger.addHandler(fileh)

        logger.setLevel(level)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(self.__CustomFormatter())
        logger.addHandler(ch)

        return logger

    @staticmethod
    def __parse_args(argv: Optional[Sequence[str]] = None, modulators=None, demodulators=None) -> dict:
        """
        this method prepares argument parser and helper to work
        :param argv: system arguments
        :param modulators: implemented modulators in form {<name>:<class>,...}
        :param demodulators: implemented demodulators in form {<name>:<class>,...}
        :return: dict containing returned arguments
        """
        if demodulators is None:
            demodulators = {}
        if modulators is None:
            modulators = {}
        parser = argparse.ArgumentParser(
            prog=f"python{3 if os.name == 'posix' else ''} {str(sys.modules['__main__'].__file__).split('/')[-1]}",
            description='this program can modulate and demodulate data in various formats such as fsk, ask and others',
            epilog='have fun')

        subparsers = parser.add_subparsers(title="commands",
                                           description="to make this program run you need to choose one of the modes:",
                                           dest="command")
        subparsers.required = True

        modulate_parser = subparsers.add_parser("modulate",
                                                help="this command will force program to modulate "
                                                     "given byte array into sound wave")

        demodulate_parser = subparsers.add_parser("demodulate",
                                                  help="this command will force program to demodulate "
                                                       "given sound wave to byte array")

        modulate_parser.add_argument('-m',
                                     "--mode",
                                     type=str,
                                     required=False,
                                     help="modulation protocol type",
                                     choices=[key for key, value in modulators.items()])

        demodulate_parser.add_argument('-m',
                                       "--mode",
                                       type=str,
                                       required=False,
                                       help="demodulation protocol type",
                                       choices=[key for key, value in demodulators.items()])

        modulate_parser.add_argument('-i',
                                     "--input",
                                     type=str,
                                     required=True,
                                     help="input file or data string")

        demodulate_parser.add_argument('-i',
                                       "--input",
                                       type=str,
                                       required=True,
                                       help="input audio file or data string")

        modulate_parser.add_argument('-o',
                                     "--output",
                                     type=str,
                                     required=False,
                                     help="path where audio file should be saved (ignore if empty) (needs to be .wav ext)")

        demodulate_parser.add_argument('-o',
                                       "--output",
                                       type=str,
                                       required=False,
                                       help="path where bin file should be saved (ignore if empty) (needs to be .bin ext)")

        modulate_parser.add_argument('-p',
                                     "--play",
                                     default=False,
                                     required="--mode" in sys.argv,
                                     help="output type: <file/audio>",
                                     action="store_true")

        parser.add_argument('-r',
                            "--raw",
                            required=False,
                            default=False,
                            help="only modulation/demodulation output will be printed if set to true",
                            action="store_true")

        parser.add_argument('-v',
                            "--verbose",
                            required=False,
                            default=False,
                            help="will print out detailed information",
                            action="store_true")

        parser.add_argument('-a',
                            "--analise",
                            required=False,
                            default=None,
                            help="will analise modulated/demodulated data and save it to given path",
                            type=str)

        parser.add_argument('-s',
                            "--show",
                            required=False,
                            default=False,
                            help="will show out performed analysis",
                            action="store_true")

        return vars(parser.parse_args(argv))

    @staticmethod
    def __load_package(package_type) -> dict:
        """
        this method loads all implemented classes of type <package_type> and return them as a dict
        :param package_type:
        :return:
        """
        package = {}
        p_name = f"../{str(package_type.__name__).lower()}s"

        modules = []
        for file in glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{p_name}/*.py")):
            sys.path.append(f"{os.path.join(os.path.dirname(os.path.abspath(__file__)))}/{p_name}")
            modules.append(__import__(os.path.splitext(os.path.basename(file))[0]))

        for module in modules:
            for name, obj in inspect.getmembers(module):
                if not inspect.isclass(obj):
                    continue
                if not issubclass(obj, package_type):
                    continue
                if obj == package_type:
                    continue

                package[name] = obj
        return package

    def __load_data_to_bytearray(self, data: str) -> Binary:
        is_file = os.path.isfile(data)

        if not is_file and data.count("/") and data.count("."):
            self.__logger.warning("input data looks like path but does not exist (path will be interpreted as data")

        if is_file:
            with open(data, "rb") as file:
                content = bytearray(file.read())
        else:
            content = bytearray(data.encode("utf-8"))
        self.__logger.debug(f"content: {content}")

        return Binary(content)

    def __decode_samples_from_file(self, filepath) -> Audio:
        self.__logger.info("opening audio file...")
        ifile = wave.open(filepath)
        samples = ifile.getnframes()
        audio = ifile.readframes(samples)

        sample_rate = ifile.getframerate()


        # Convert buffer to float32 using NumPy
        audio_as_np_int16 = np.frombuffer(audio, dtype=np.int16)
        audio_as_np_float32 = audio_as_np_int16.astype(np.float32)

        # Normalise float32 array so that values are between -1.0 and +1.0
        max_int16 = 2 ** 15
        audio_normalised = audio_as_np_float32 / max_int16

        samples_amount = len(audio_normalised)
        audio_length = samples_amount / sample_rate

        return Audio(audio_normalised, sample_rate, samples_amount, audio_length)
