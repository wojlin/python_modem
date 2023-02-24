import numpy as np
from dataclasses import dataclass
import json

from interfaces import Modulator


class Binary:
    def __init__(self, input_bin: bytearray):
        self.__input_bin = input_bin
        self.__bin = self.__to_bin()

    def getSize(self):
        return len(self.__bin)

    def getBin(self):
        return self.__bin

    def getByteArray(self):
        return self.__input_bin

    def __repr__(self):
        count = 0
        data = ""
        for symbol in self.__bin:
            if count == 8:
                data += '\n'
                count = 0
            data += str(symbol)
            count += 1
        return data

    def __to_bin(self):
        data = ""
        for symbol in self.__input_bin:
            symbol_bin = '{0:08b}'.format(symbol)
            data += symbol_bin
        new_data = [int(x) for x in data]
        return new_data


@dataclass
class ModulatedData:
    modulator: Modulator
    times: list
    samples: list
    sample_rate: int
    data: Binary


def load_config(filepath: str) -> dict:
    json_data = {}
    with open(filepath) as f:
        json_data = json.loads(f.read())
    data = type("data", (), json_data)
    return json_data









