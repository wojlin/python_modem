from typing import Sequence, Optional
from matplotlib import pyplot as plt

from processing_hub import ModulatorHub, DemodulatorHub
from program_core import program_core
from utils import ModulatedData, DemodulatedData


def main(argv: Optional[Sequence[str]] = None) -> int:
    core = program_core(argv)
    data = core.getData()

    logger = data.logger

    logger.info("init stage complete!")
    command = data.args["command"]
    processing_mode = data.args["mode"]

    """
    -v modulate -m ASK --i "/PROJECTS/python_modem/tests/ascii_short" -o "tests/output.wav" -p
    -v demodulate -m ASK --i "/PROJECTS/python_modem/tests/output.wav" -o "tests/output.bin"
    -v demodulate -m ASK --i "/PROJECTS/python_modem/tests/output_noisy.wav" -o "tests/output.bin"
    
    python3 main.py -v -a "/home/anon/PROJECTS/python_modem/tests/temp/analysis_mod.png" -s modulate -m ASK --i "/home/anon/PROJECTS/python_modem/tests/ascii_short" -o "tests/temp/output.wav" -p
    python3 main.py -v -a "/home/anon/PROJECTS/python_modem/tests/temp/analysis_demod.png" -s demodulate -m ASK --i "/home/anon/PROJECTS/python_modem/tests/temp/output.wav" -o "tests/temp/output.txt"
    
    """

    if command == "modulate":
        hub = ModulatorHub(logger=logger, processing_type="Modulator", processing_mode=processing_mode)
        binary_encoded_data = hub.encode_data(data.data)
        modulated_data: ModulatedData = hub.modulate(binary_encoded_data, data.modulators[processing_mode])

        if data.args["output"]:
            hub.save(modulated_data, data.args["output"])

        if data.args["play"]:
            hub.play(modulated_data)

        if data.args["analise"] or data.args["show"]:
            hub.analise_modulated_data(modulated_data)

    elif command == "demodulate":
        hub = DemodulatorHub(logger=logger, processing_type="Demodulator", processing_mode=processing_mode)
        demodulated_data: DemodulatedData = hub.demodulate(data.data, data.demodulators[processing_mode])

        logger.info(f"demodulated data: '{demodulated_data.demodulated_data.decode()}'")
        if data.args["output"]:
            hub.save(demodulated_data, data.args["output"])

        if data.args["analise"] or data.args["show"]:
            hub.analise_demodulated_data(demodulated_data)
    else:
        raise TypeError(f"program can be run either in modulate or demodulate mode! '{command}' is not valid")

    if data.args["analise"]:
        logger.info(f"saving analysis to '{data.args['analise']}'")
        plt.savefig(data.args["analise"])

    if data.args["show"]:
        logger.info("showing analysis...")
        plt.show()

    exit_code = 0
    logger.debug(f"exiting with exit code {exit_code}")

    return exit_code


if __name__ == "__main__":
    exit(main())
