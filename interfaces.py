from abc import ABC, abstractmethod


class Modulator(ABC):
    @abstractmethod
    def modulate(self, input_binary):
        pass


class Demodulator(ABC):
    @abstractmethod
    def demodulate(self, input_binary):
        pass

