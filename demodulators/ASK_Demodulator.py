import copy

import matplotlib.pyplot as plt
import numpy as np
import math
from scipy import signal

from interfaces import Demodulator
from utils import Audio, DemodulatedData, PacketGraphicalInfo, PacketGraphicalInfoSpan


class ASK(Demodulator):
    def __init__(self, logger, config, comm_config):
        logger.debug("ASK demodulation init")
        self.logger = logger
        self.config = config
        self.comm_config = comm_config

    def demodulate(self, audio: Audio):
        self.logger.debug("ASK demodulation started")
        self.logger.debug(f"ASK demodulation loaded config: '{self.config}'")

        audio_samples = audio.getSamples()
        samples = copy.copy(audio_samples)
        sample_rate = audio.getSampleRate()
        audio_length = audio.getAudioLength()
        samples_amount = audio.getSamplesAmount()
        baud_rate = self.comm_config["baud_rate[bps]"]

        main_freq = self.__find_main_frequency(samples, sample_rate, samples_amount)

        self.logger.debug(f"audio length: {round(audio_length,2)}s")
        self.logger.debug(f"found main frequency at: {int(main_freq)}Hz")

        samples = self.__apply_filters(samples, main_freq, sample_rate)
        samples = np.abs(signal.hilbert(samples))
        samples = signal.medfilt(samples, 5)
        samples = [1 if sample > 0.5 else 0 for sample in samples]

        dividor = 10

        new_samples = []
        for idx, sample in enumerate(samples):
            if idx % dividor == 0:
                new_samples.append(sample)

        samples = new_samples
        samples_amount = len(samples)
        sample_rate = sample_rate / dividor
        audio_len = samples_amount / sample_rate
        one_bit_time = 1 / baud_rate
        samples_per_bit = int(one_bit_time * samples_amount / audio_len)

        packets_start_point = self.__find_starting_sample(samples, samples_per_bit, self.comm_config)
        #print(packets_start_point)

        bits_in_packet = (self.comm_config["packet_len[bytes]"] + 3 if self.comm_config["crc8_sum"] else 2) * 8
        samples_per_packet = samples_per_bit * bits_in_packet

        data_packets = []
        for idx, data_pack_start in enumerate(packets_start_point):
            data_packets.append(samples[data_pack_start: data_pack_start + samples_per_packet])

        raw_bits = []
        data = []
        for packet in data_packets:
            packet_data = []
            for i in range(bits_in_packet):
                bit_value = round(np.average(packet[i*samples_per_bit:i*samples_per_bit+samples_per_bit]))
                raw_bits.append(bit_value)
                packet_data.append(bit_value)
            data.append(packet_data)


        bytes_list = []

        data_bytes = (self.comm_config["packet_len[bytes]"] + 1 if self.comm_config["crc8_sum"] else 0)

        for packet in data:
            bytes_array = []
            bits_array = []
            for bit in packet:
                bits_array.append(bit)
                if len(bits_array) == 8:
                    str_repr = ''.join(str(bit) for bit in bits_array)
                    bytes_array.append(int(str_repr, 2))
                    bits_array = []
            bytes_list.append(bytes_array[1:data_bytes+0])  # #############  add +1 (skipping crc)!!!!!

        output_bytes = [item for sublist in bytes_list for item in sublist]

        packet_list = []
        binaries_list = []
        for start_point in packets_start_point:
            packet_list.append(start_point)
            plt.axvline(start_point, color="red")

            for i in range(bits_in_packet):
                point_left = start_point+(i*samples_per_bit)
                point_right = start_point+((i+1)*samples_per_bit)

                binaries_list.append(PacketGraphicalInfoSpan(point_left, point_right, raw_bits[0]))
                raw_bits.pop(0)

        demodulated_data = bytearray(output_bytes)
        
        for i in reversed(range(len(demodulated_data))):
            if demodulated_data[i] == 0:
                demodulated_data.pop()
            else:
                break

        return DemodulatedData(demodulator=self,
                               digital_samples=samples,
                               demodulated_data=demodulated_data,
                               bytes_list=PacketGraphicalInfo(packet_list, binaries_list),
                               audio=audio)

    @staticmethod
    def __find_starting_sample(samples, samples_per_bit, comm_config):

        start_byte = '{0:08b}'.format(comm_config["start_byte"])
        start_pattern = []
        for _byte in start_byte:
            for x in range(samples_per_bit):
                start_pattern.append(int(_byte))

        signalshifted = [float(x) - 0.5 for x in samples]
        syncA = [float(x) - 0.5 for x in start_pattern]

        peaks = [(0, 0)]
        mindistance = len(start_pattern) * (comm_config["packet_len[bytes]"] + 3 if comm_config["crc8_sum"] else 2)

        for i in range(len(samples) - len(syncA)):
            corr = np.dot(syncA, signalshifted[i: i + len(syncA)])

            # if previous peak is too far, keep it and add this value to the
            # list as a new peak
            if i - peaks[-1][0] > mindistance:
                peaks.append((i, corr))

            # else if this value is bigger than the previous maximum, set this
            # one
            elif corr > peaks[-1][1]:
                peaks[-1] = (i, corr)

        start_peaks = []
        for i in range(len(peaks)):
            if peaks[i][1] > 0:
                start_peaks.append(peaks[i][0])

        return start_peaks


    @staticmethod
    def __find_main_frequency(samples, sample_rate, samples_amount):
        fft_data = abs(np.fft.rfft(samples)) ** 2
        # find the maximum
        which = fft_data[1:].argmax() + 1
        # use quadratic interpolation around the max
        if which != len(fft_data) - 1:
            y0, y1, y2 = np.log(fft_data[which - 1:which + 2:])
            x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
            # find the frequency and output it
            the_freq = (which + x1) * sample_rate / samples_amount
            return the_freq
        else:
            the_freq = which * sample_rate / samples_amount
            return the_freq

    @staticmethod
    def __apply_filters(samples, frequency, sample_rate):
        offset = 100
        _cut_freq = frequency + offset
        _order = 2
        nyq = 0.5 * sample_rate
        normal_cutoff = _cut_freq / nyq
        # Get the filter coefficients
        b, a = signal.butter(_order, normal_cutoff, btype='low', analog=False, output='ba')  # noqa
        samples = signal.filtfilt(b, a, samples)

        _cut_freq = frequency - offset
        _order = 2
        nyq = 0.5 * sample_rate
        normal_cutoff = _cut_freq / nyq
        # Get the filter coefficients
        b, a = signal.butter(_order, normal_cutoff, btype='high', analog=False, output='ba')  # noqa
        samples = signal.filtfilt(b, a, samples)

        samples /= np.max(np.abs(samples), axis=0)

        return samples
