from typing import Sequence, Optional

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
    """

    if command == "modulate":
        hub = ModulatorHub(logger=logger, processing_type="Modulator", processing_mode=processing_mode)
        binary_encoded_data = hub.encode_data(data.data)
        modulated_data: ModulatedData = hub.modulate(binary_encoded_data, data.modulators[processing_mode])

        if data.args["output"]:
            hub.save(modulated_data, data.args["output"])

        if data.args["play"]:
            hub.play(modulated_data)

        hub.analise_modulated_data(modulated_data)

    elif command == "demodulate":
        hub = DemodulatorHub(logger=logger, processing_type="Demodulator", processing_mode=processing_mode)
        demodulated_data: DemodulatedData = hub.demodulate(data.data, data.demodulators[processing_mode])

        if data.args["output"]:
            hub.save(demodulated_data, data.args["output"])

        hub.analise_demodulated_data(demodulated_data)
    else:
        raise TypeError(f"program can be run either in modulate or demodulate mode! '{command}' is not valid")

    return 0


if __name__ == "__main__":
    exit(main())
