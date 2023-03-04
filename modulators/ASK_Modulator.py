from scipy.signal import butter, filtfilt
import numpy as np
import sys

from deeper_code.utils import Binary
from deeper_code.interfaces import Modulator


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
        start_silence = self.config["silence_at_start[s]"]
        end_silence = self.config["silence_at_end[s]"]

        data = input_binary.getBin()
        data_len = input_binary.getSize()

        if data_len < 1000:
            self.logger.debug(f"data to modulate: \n{input_binary}")
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
                samples[x] = samples[x] * one_symbol_amplitude if data[i] == 1 else samples[x] * zero_symbol_amplitude

        # TODO: make better start padding

        samples = np.insert(samples, 0, [0 for x in range(int(start_silence*1000))])
        times = [t+start_silence for t in times]
        times = np.insert(times, 0, [x*start_silence for x in range(int(start_silence*1000))])

        samples = np.append(samples, [0 for x in range(int(end_silence * 1000))], axis=0)
        times = np.append(times, [times[-1] + x / 1000 for x in range(int(end_silence * 1000))], axis=0)

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

        return times, samples, sample_rate, self
