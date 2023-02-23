from interfaces import Modulator
import numpy as np
import sys

from utils import Binary


class ASK(Modulator):
    def __init__(self, logger, config):
        logger.debug("ASK modulation init")
        self.logger = logger
        self.config = config

    def modulate(self, input_binary: Binary):
        self.logger.debug("ASK modulation started")
        self.logger.debug(f"ASK modulation loaded config: '{self.config}'")

        sample_rate = self.config["sample_rate[Hz]"]
        frequency = self.config["carrier_frequency[Hz]"]
        baud_rate = self.config["baud_rate[bps]"]

        data = input_binary.getBin()
        data_len = input_binary.getSize()

        if data_len < 1000:
            self.logger.debug(f"data to demodulate: \n{input_binary}")
        self.logger.debug(f"data length: {data_len} symbols")

        theta = 0
        amplitude = 1

        start_time = 0
        end_time = data_len / baud_rate

        self.logger.debug(f"modulated data length: {end_time}s")

        time = np.arange(start_time, end_time, 1 / sample_rate)

        np.set_printoptions(threshold=sys.maxsize)

        times = time
        samples = amplitude * np.sin(2 * np.pi * frequency * time + theta)

        for i in range(len(data)):
            if not data[i] == 0:
                continue

            left_band = np.ceil(i * (sample_rate / baud_rate)).astype(int)
            right_band = np.ceil((i + 1) * (sample_rate / baud_rate)).astype(int)
            if right_band > len(samples):
                right_band = len(samples)
            for x in range(left_band, right_band):
                samples[x] = 0

        self.logger.info("modulation complete!")

        return times, samples, sample_rate, self.__class__.__name__
