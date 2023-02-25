import numpy as np
from dataclasses import dataclass
import json

from interfaces import Modulator, Demodulator


class Binary:
    def __init__(self, input_bin: bytearray):
        self.__input_bin = input_bin
        self.__bin = self.__to_bin()
        self.__str = self.__to_str()

    def getSize(self):
        return len(self.__bin)

    def getStr(self):
        return self.__str

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

    def __to_str(self):
        return ''.join([str(x) for x in self.__bin])


class Audio:
    def __init__(self, samples, sample_rate, samples_amount, audio_length):
        self.__sample_rate = sample_rate
        self.__samples = samples
        self.__samples_amount = samples_amount
        self.__audio_length = audio_length

    def getSamples(self):
        return self.__samples

    def getSampleRate(self):
        return self.__sample_rate

    def getSamplesAmount(self):
        return self.__samples_amount

    def getAudioLength(self):
        return self.__audio_length



@dataclass
class PacketGraphicalInfoSpan:
    start_point: int
    end_point: int
    value: int
@dataclass
class PacketGraphicalInfo:
    packets_start: list
    binaries: list[PacketGraphicalInfoSpan]

@dataclass
class DemodulatedData:
    demodulator: Demodulator
    digital_samples: list
    demodulated_data: bytearray
    bytes_list: PacketGraphicalInfo
    audio: Audio


@dataclass
class ModulatedData:
    modulator: Modulator
    times: list
    samples: list
    sample_rate: int
    data: Binary


def load_config(filepath: str) -> dict:
    with open(filepath) as f:
        return json.loads(f.read())









