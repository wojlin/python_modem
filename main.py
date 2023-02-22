from typing import Sequence, Optional
import logging
import os

from interfaces import Modulator, Demodulator
from program_core import program_core


class ModulatorHub:
    def __init__(self, logger):
        self.logger = logger

    def analize_modulated_data(self, output_samples):
        print(f"analizing {output_samples}")

    def modulate(self, input_binary: bytearray, modulator_type: type(Modulator)):
        print("modulating")
        modulator = modulator_type(self.logger)
        return modulator.modulate(input_binary)

    def play(self, samples: list):
        if not samples:
            self.logger.error("samples cannot be empty")
            return

        self.logger.info("playing modulated data")


def main(argv: Optional[Sequence[str]] = None) -> int:
    core = program_core(argv)
    data = core.getData()

    logger = data.logger

    logger.info("init stage complete!")
    command = data.args["command"]

    if command == "modulate":
        hub = ModulatorHub(logger)
        hub.modulate(data, data.modulators[data.args["mode"]])
    elif command == "demodulate":
        raise NotImplementedError("demodulation not implemented yet")
    else:
        raise TypeError(f"program can be run either in modulate or demodulate mode! '{command}' is not valid")

    return 0


if __name__ == "__main__":
    exit(main())
