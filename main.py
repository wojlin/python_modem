from typing import Sequence, Optional
import logging

from interfaces import Modulator, Demodulator
from utils import parse_args, load_package, configure_logging


class ModulatorHub:
    def analize_modulated_data(self, output_samples):
        print(f"analizing {output_samples}")

    def modulate(self, input_binary: bytearray, modulator_type: type(Modulator)):
        print("modulating")
        modulator = modulator_type()
        return modulator.modulate(input_binary)


def main(argv: Optional[Sequence[str]] = None) -> int:

    modulators = load_package(Modulator)
    demodulators = load_package(Demodulator)

    args = parse_args(argv, modulators, demodulators)

    logger = configure_logging(args)

    logger.debug("test")
    logger.info("test1")
    logger.warning("test2")
    logger.error("test3")
    logger.info(f"received app run args: {args}")
    logger.info(f"loaded modulators: {', '.join([mod for mod, cls in modulators.items()])}")
    logger.info(f"loaded demodulators: {', '.join([mod for mod, cls in demodulators.items()])}")

    if args["command"] == "modulate":
        hub = ModulatorHub()
        hub.modulate(bytearray("hello world".encode("ASCII")), modulators["FSK"])
    elif args["command"] == "demodulate":
        raise NotImplementedError("demodulation not implemented yet")
    else:
        raise TypeError(f"program can be run either in modulate or demodulate mode! '{args['command']}' is not valid")

    return 0


if __name__ == "__main__":
    exit(main())
