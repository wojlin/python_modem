import copy
import time
import math
import numpy as np
from scipy import signal
from crc import Calculator, Crc8

from modem.interfaces import Demodulator
from modem.utils import Audio, DemodulatedData, DataSector


class ASK(Demodulator):
    def __init__(self, logger, config, comm_config):
        logger.debug("ASK demodulation init")
        self.logger = logger
        self.config = config
        self.comm_config = comm_config

    def demodulate(self, audio: Audio):
        def wrapper():
            start_time = time.time()
            data = self.__demodulate(audio)
            end_time = time.time()
            self.logger.info(f"message demodulated in {round(end_time - start_time, 2)}s")
            return data

        return wrapper()

    def __demodulate(self, audio: Audio):
        self.logger.debug("ASK demodulation started")
        self.logger.debug(f"ASK demodulation loaded config: '{self.config}'")

        audio_samples = audio.getSamples()
        samples = copy.copy(audio_samples)
        sample_rate = audio.getSampleRate()
        audio_length = audio.getAudioLength()
        samples_amount = audio.getSamplesAmount()
        baud_rate = self.comm_config["baud_rate[bps]"]
        samples_per_bit = int(samples_amount / (baud_rate * audio_length))
        use_crc = self.comm_config["crc8_sum"]
        bytes_per_packet = (self.comm_config["packet_len[bytes]"] + 3 if use_crc else 2)
        packet_len = self.comm_config["packet_len[bytes]"]

        main_freq = self.__find_main_frequency(samples, sample_rate, samples_amount)

        self.logger.debug(f"audio length: {round(audio_length, 2)}s")
        self.logger.debug(f"found main frequency at: {int(main_freq)}Hz")

        if self.config["apply_frequency_cut"]:
            samples = self.__apply_filters(samples, main_freq, sample_rate)
        samples = np.abs(signal.hilbert(samples))
        if self.config["apply_filters"]:
            samples = signal.medfilt(samples, 5)
        samples = [1 if sample > self.config["one_symbol_amplitude"] else 0 for sample in samples]

        sectors = self.__samples_to_sectors(samples)
        packets, bits_analysis = self.__sectors_to_packets(sectors, samples_per_bit, bytes_per_packet)
        data, crc_check = self.__packets_to_data(packets, packet_len, use_crc)

        if not crc_check:
            self.logger.critical("crc failed!")

        return DemodulatedData(demodulator=self,
                               digital_samples=samples,
                               demodulated_data=data,
                               bits_analysis=bits_analysis,
                               audio=audio,
                               crc_check_pass=crc_check)

    def __samples_to_sectors(self, samples):
        samples = np.array(copy.copy(samples))
        centers, plateaus = signal.find_peaks(samples, plateau_size=1)

        sectors = []
        for point in zip(plateaus["left_edges"], plateaus["right_edges"], centers, plateaus["plateau_sizes"]):
            sector = DataSector(left_edge=point[0],
                                right_edge=point[1],
                                center=point[2],
                                width=point[3],
                                value=1)
            sectors.append(sector)

        for i in reversed(range(1, len(sectors))):
            point1 = sectors[i]
            point2 = sectors[i - 1]
            left_edge = point2.right_edge
            right_edge = point1.left_edge
            width = right_edge - left_edge
            center = left_edge + int(width / 2)
            new_sector = DataSector(left_edge=left_edge,
                                    right_edge=right_edge,
                                    center=center,
                                    width=width,
                                    value=0)
            sectors.insert(i, new_sector)

        return sectors

    def __sectors_to_packets(self, sectors, samples_per_bit, bytes_per_packet):
        bits_data = []
        bits_list = []
        for sector in sectors:
            bits_amount = round(sector.width / samples_per_bit)
            bits_amount = 1 if bits_amount == 0 else bits_amount
            for x in range(bits_amount):
                bits_list.append(sector.value)

                left_edge = sector.left_edge+(samples_per_bit*x)
                right_edge = sector.left_edge + (samples_per_bit * (x+1))
                width = right_edge - left_edge
                value = sector.value
                center = int(left_edge + (width / 2))
                bit_data = DataSector(left_edge=left_edge,
                                      right_edge=right_edge,
                                      width=width,
                                      value=value,
                                      center=center)

                bits_data.append(bit_data)

        bytes_list = [bits_list[i * 8:i * 8 + 8] for i in range(round(len(bits_list) / 8))]

        packets_list = [bytes_list[i * bytes_per_packet:i * bytes_per_packet + bytes_per_packet] for i in
                        range(round(len(bytes_list) / bytes_per_packet))]

        return self.__replace_bits_with_byte_in_packets(packets_list), bits_data

    @staticmethod
    def __replace_bits_with_byte_in_packets(packets):
        for packet in range(len(packets)):
            for byte in range(len(packets[packet])):
                packets[packet][byte] = int(''.join([str(bit) for bit in packets[packet][byte]]), 2)
        return packets

    def __packets_to_data(self, packets, packet_len, use_crc):
        try:
            data = bytearray()
            calculator = Calculator(Crc8.CCITT)
            crc_check = True
            for packet in range(len(packets)):
                data_in_packet = packets[packet][1:packet_len + 1]

                for byte in data_in_packet:
                    data.append(byte)

                if use_crc:
                    crc_value = packets[packet][packet_len + 1]
                    if not self.__check_crc(packet, calculator, bytearray(data_in_packet), crc_value):
                        crc_check = False

            data = self.__remove_null_from_data(data)

            return data, crc_check
        except Exception:
            self.logger.error("failed to decode bytes from samples")
            return [], False

    def __check_crc(self, packet_n, calculator, value, crc):
        value_crc = calculator.checksum(value)
        if value_crc == crc:
            self.logger.debug(f"crc sum for packet '{packet_n}' correct!")
            return True
        else:
            self.logger.error(f"crc sum for packet '{packet_n}' is incorrect! received: {value_crc} expected: {crc}")
            return False

    @staticmethod
    def __remove_null_from_data(data):
        data = data
        for i in reversed(range(len(data))):
            if data[i] == 0:
                data.pop()
            else:
                break
        return data

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
