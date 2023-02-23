from interfaces import Modulator
import numpy as np


class ASK(Modulator):
    def __init__(self, logger, config):
        logger.debug("ASK modulation init")
        self.logger = logger
        self.config = config

    def modulate(self, input_binary):
        self.logger.debug("ASK modulation started")
        self.logger.debug(f"ASK modulation loaded config: '{self.config}'")

        sample_rate = self.config["sample_rate[Hz]"]
        frequency = self.config["carrier_frequency[Hz]"]
        baud_rate = self.config["baud_rate[bps]"]

        theta = 0
        amplitude = 1

        start_time = 0
        end_time = len(input_binary) / baud_rate * sample_rate
        time = np.arange(start_time, end_time, 1 / sample_rate)

        samples = amplitude * np.sin(2 * np.pi * frequency * time + theta)


        return samples
