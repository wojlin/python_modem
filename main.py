from glob import glob
import inspect
import getopt
import sys
import os

from interfaces import Modulator, Demodulator


class ModulatorHub:
    def analize_modulated_data(self, output_samples):
        print(f"analizing {output_samples}")

    def modulate(self, input_binary: bytearray, modulator_type: type(Modulator)):
        print("modulating")
        modulator = modulator_type()
        return modulator.modulate(input_binary)


def load_package(package_type) -> dict:
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


if __name__ == "__main__":
    modulators = load_package(Modulator)
    demodulators = load_package(Demodulator)
    print(modulators)
    print(demodulators)

    hub = ModulatorHub()
    hub.modulate(bytearray("hello world".encode("ASCII")), modulators["FSK"])