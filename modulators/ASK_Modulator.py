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

        cycles_per_symbol = self.config["cycles_per_symbol"]  # how many sine cycles
        resolution = self.config["datapoints_per_cycle"]  # how many datapoints to generate

        length = np.pi * 2 * cycles_per_symbol
        samples = np.sin(np.arange(0, length, length / resolution))

        return samples
