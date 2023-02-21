from typing import Sequence, Optional
from glob import glob
import argparse
import inspect
import sys
import os


def parse_args(argv: Optional[Sequence[str]] = None, modulators=None, demodulators=None) -> dict:
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
        prog=f"python{3 if os.name == 'posix' else ''} {os.path.basename(__file__)}",
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

    return vars(parser.parse_args(argv))


def load_package(package_type) -> dict:
    """
    this method loads all implemented classes of type <package_type> and return them as a dict
    :param package_type:
    :return:
    """
    package = {}
    p_name = f"{package_type.__name__}s"

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
