from typing import Sequence, Optional

from processing_hub import ModulatorHub, DemodulatorHub
from program_core import program_core
from utils import ModulatedData


def main(argv: Optional[Sequence[str]] = None) -> int:
    core = program_core(argv)
    data = core.getData()

    logger = data.logger

    logger.info("init stage complete!")
    command = data.args["command"]
    processing_mode = data.args["mode"]

    if command == "modulate":
        hub = ModulatorHub(logger=logger, processing_type="Modulator", processing_mode=processing_mode)
        times, samples, sample_rate, class_name = hub.modulate(data.data, data.modulators[processing_mode])
        modulated_data = ModulatedData(class_name, times, samples, sample_rate, data.data)
        hub.analise_modulated_data(modulated_data)
        if data.args["play"]:
            hub.play(samples)
    elif command == "demodulate":
        hub = DemodulatorHub(logger=logger, processing_type="Demodulator", processing_mode=processing_mode)
        hub.demodulate(data, data.modulators[processing_mode])
        raise NotImplementedError("demodulation not implemented yet")
    else:
        raise TypeError(f"program can be run either in modulate or demodulate mode! '{command}' is not valid")

    return 0


if __name__ == "__main__":
    exit(main())
