from typing import Sequence, Optional

from interfaces import Modulator, Demodulator
from utils import parse_args, load_package


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

    print(args)

    print(modulators)
    print(demodulators)

    hub = ModulatorHub()
    hub.modulate(bytearray("hello world".encode("ASCII")), modulators["FSK"])

    return 0


if __name__ == "__main__":
    exit(main())
