from abc import ABC, abstractmethod


class Modulator(ABC):
    @abstractmethod
    def __init__(self, logger):
        pass

    @abstractmethod
    def modulate(self, input_binary):
        pass


class Demodulator(ABC):
    @abstractmethod
    def __init__(self, logger):
        pass

    @abstractmethod
    def demodulate(self, input_binary):
        pass

