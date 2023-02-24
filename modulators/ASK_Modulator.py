from scipy.signal import butter, lfilter, freqz, filtfilt
import numpy as np
import sys

from utils import Binary
from interfaces import Modulator


class ASK(Modulator):
    def __init__(self, logger, config, comm_config):
        logger.debug("ASK modulation init")
        self.logger = logger
        self.config = config
        self.comm_config = comm_config

    def modulate(self, input_binary: Binary):
        self.logger.debug("ASK modulation started")
        self.logger.debug(f"ASK modulation loaded config: '{self.config}'")

        sample_rate = self.config["sample_rate[Hz]"]
        frequency = self.config["carrier_frequency[Hz]"]
        baud_rate = self.comm_config["baud_rate[bps]"]
        one_symbol_amplitude = self.config["one_symbol_amplitude"]
        zero_symbol_amplitude = self.config["zero_symbol_amplitude"]

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
            left_band = np.ceil(i * (sample_rate / baud_rate)).astype(int)
            right_band = np.ceil((i + 1) * (sample_rate / baud_rate)).astype(int)
            if right_band > len(samples):
                right_band = len(samples)
            for x in range(left_band, right_band):
                samples[x] = samples[x] * one_symbol_amplitude if data[i] == 1 else zero_symbol_amplitude

        self.logger.info("applying filter...")

        apply_filters = True

        if apply_filters:
            offset = 100
            _cut_freq = frequency + offset
            _order = 2
            nyq = 0.5 * sample_rate
            normal_cutoff = _cut_freq / nyq
            # Get the filter coefficients
            b, a = butter(_order, normal_cutoff, btype='low', analog=False, output='ba')  # noqa
            samples = filtfilt(b, a, samples)

            _cut_freq = frequency - offset
            _order = 2
            nyq = 0.5 * sample_rate
            normal_cutoff = _cut_freq / nyq
            # Get the filter coefficients
            b, a = butter(_order, normal_cutoff, btype='high', analog=False, output='ba')  # noqa
            samples = filtfilt(b, a, samples)

            samples /= np.max(np.abs(samples), axis=0)

        self.logger.info("modulation complete!")

        return times, samples, sample_rate, self.__class__.__name__
