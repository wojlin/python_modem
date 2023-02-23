from matplotlib import pyplot as plt
from matplotlib import figure
import sounddevice as sd
import os

from interfaces import Modulator, Demodulator
from utils import load_config


class HUB:
    def __init__(self, logger, processing_type, processing_mode):
        self.logger = logger
        self.processing_type = processing_type
        self.processing_mode = processing_mode
        self.config = self.find_processing_config()

    def find_processing_config(self):
        config_path = f"configs/{self.processing_mode}_{self.processing_type}.json"
        is_file = os.path.isfile(config_path)
        if not is_file:
            config = None
            self.logger.warning(f"'{config_path}' config for {self.processing_mode} {self.processing_type} not found")
        else:
            config = load_config(config_path)

        return config


class ModulatorHub(HUB):

    def analise_modulated_data(self, output_samples):
        self.logger.info("analysing modulated data")
        plt.plot(output_samples)

    def modulate(self, input_binary: bytearray, modulator_type: type(Modulator)):
        self.logger.debug("pre modulation init")

        modulator = modulator_type(self.logger, self.config)
        return modulator.modulate(input_binary)

    def play(self, samples: list):
        if not samples:
            self.logger.error("samples cannot be empty")
            return
        #sd.play(samples, fs)

        self.logger.info("playing modulated data")


class DemodulatorHub(HUB):

    def demodulate(self, input_samples: list, modulator_type: type(Demodulator)):
        self.logger.debug("pre demodulation init")