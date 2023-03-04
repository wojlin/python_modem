from typing import Sequence, Optional
from matplotlib import pyplot as plt
import argparse
import logging
import pickle
import sys
import os

import deeper_code.utils
from deeper_code.utils import DemodulatedData, ModulatedData
from deeper_code.processing_hub import DemodulatorHub, ModulatorHub

def configure_logging():
    logger = logging.getLogger("analise")
    formatter = logging.Formatter(
        '%(asctime)s %(msecs)03dms - (%(filename)s:%(lineno)d) - %(levelname)s - %(message)s ')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def main(argv: Optional[Sequence[str]] = None) -> int:

    '''
    python3 analise.py --input "/home/anon/PROJECTS/python_modem/tests/temp/analysis_demod.pickle"
    '''

    logger = configure_logging()

    sys.path.append(f"{os.path.join(os.path.dirname(os.path.abspath(__file__)))}/modulators/")
    sys.path.append(f"{os.path.join(os.path.dirname(os.path.abspath(__file__)))}/demodulators/")

    parser = argparse.ArgumentParser(
        prog=f"python{3 if os.name == 'posix' else ''} {str(sys.modules['__main__'].__file__).split('/')[-1]}",
        description='use this script to view saved analysis data')

    parser.add_argument('-i',
                        "--input",
                        required=True,
                        default=False,
                        help="path to saved .pickle file")

    args = vars(parser.parse_args(argv))

    filepath = args["input"]
    if os.path.isfile(filepath):
        with open(filepath, 'rb') as file:
            pickled_data = pickle.loads(file.read())
    else:
        logger.critical(f"'{filepath}'file does not exist!")
        raise FileNotFoundError(f"'{filepath}'file does not exist!")

    if type(pickled_data) == deeper_code.utils.DemodulatedData:
        logger.info("launching demodulation analysis...")
        processing_mode = pickled_data.demodulator.__class__.__name__
        logger.info(f"detected modulation type: {processing_mode}")
        hub = DemodulatorHub(logger, processing_type="Demodulator", processing_mode=processing_mode)
        hub.analise_demodulated_data(pickled_data)
    elif type(pickled_data) == deeper_code.utils.ModulatedData:
        logger.info("launching modulation analysis...")
        processing_mode = pickled_data.modulator.__class__.__name__
        logger.info(f"detected modulation type: {processing_mode}")
        hub = ModulatorHub(logger, processing_type="Modulator", processing_mode=processing_mode)
        hub.analise_modulated_data(pickled_data)
    else:
        raise TypeError("unnown")

    plt.show()

    return 0


if __name__ == "__main__":
    exit(main())
