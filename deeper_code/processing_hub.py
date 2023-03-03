from matplotlib.ticker import FormatStrFormatter
from matplotlib import pyplot as plt
from crc import Calculator, Crc8
import sounddevice as sd
import numpy as np
import struct
import copy
import wave
import os

from deeper_code.interfaces import Modulator, Demodulator
from deeper_code.utils import load_config, DemodulatedData, ModulatedData, Audio, Binary

class HUB:
    def __init__(self, logger, processing_type, processing_mode):
        self.logger = logger
        self.processing_type = processing_type
        self.processing_mode = processing_mode
        self.config = self.find_processing_config()
        self.dir_name = '/'.join(os.path.dirname(os.path.realpath(__file__)).split('/')[:-1])
        self.comm_config = load_config(f"{self.dir_name}/configs/communication_config.json")

    def find_processing_config(self):
        self.dir_name = '/'.join(os.path.dirname(os.path.realpath(__file__)).split('/')[:-1])
        config_path = f"{self.dir_name}/configs/{self.processing_mode}_{self.processing_type}.json"
        is_file = os.path.isfile(config_path)
        if not is_file:
            config = None
            self.logger.critical(f"'{config_path}' config for {self.processing_mode} {self.processing_type} not found")
            raise FileNotFoundError(f"{config_path} not exist")
        else:
            config = load_config(config_path)

        return config


class ModulatorHub(HUB):

    def analise_modulated_data(self, modulated_data: ModulatedData):
        self.logger.info("analysing modulated data")

        fig = plt.gcf()
        fig.set_size_inches(10, 8)
        fig.set_dpi(100)

        plot1 = plt.subplot2grid((10, 10), (0, 0), rowspan=3, colspan=6)
        plot1.set_title("binary data")
        plot2 = plt.subplot2grid((10, 10), (4, 0), rowspan=6, colspan=6)
        plot2.set_title("modulated data")
        plot3 = plt.subplot2grid((10, 10), (0, 7), rowspan=10, colspan=3)
        plot3.set_title("PSD")

        bin_data = copy.copy(modulated_data.data.getBin())
        bin_data.insert(0, bin_data[0])
        bin_data.append(bin_data[-1])
        plot1.step([x for x in range(len(bin_data))], bin_data, color='red')
        plot2.plot(modulated_data.times, modulated_data.samples, color="black")
        pxx, freq, line = plot3.psd(modulated_data.samples, Fs=modulated_data.sample_rate, return_line=True)

        plot1.fill_between([x for x in range(len(bin_data))], bin_data, step="pre", alpha=1, color='red')
        plot1.set_xlim(xmin=0, xmax=modulated_data.data.getSize())
        plot1.xaxis.set_ticks(np.arange(0, modulated_data.data.getSize(), 10))
        plot1.set_ylim(ymin=-0.2, ymax=1.2)
        plot1.set_yticks([0, 1])

        plot2.set_xlim(xmin=0, xmax=modulated_data.times[-1])
        space = np.arange(modulated_data.times[0], modulated_data.times[-1], modulated_data.times[-1] / 10)
        plot2.set_xticks(space)  # , labels=[f"{round(x, 2)}s" for x in space], rotation=50)

        line_x = line[0].get_xdata()
        line_y = line[0].get_ydata()
        plot3.fill_between(line_x, line_y, [min(line_y) for x in line_y],
                           alpha=0.4, color='blue')
        plot3.set_xlim(xmin=0, xmax=int(modulated_data.sample_rate / 2))
        plot3.set_ylim(ymin=-100, ymax=max(line_y) + 10)

        start_silence = modulated_data.config["silence_at_start[s]"]
        start_silence_samples = start_silence * 1000

        end_silence = modulated_data.config["silence_at_end[s]"]
        end_silence_samples = end_silence * 1000

        samples_per_byte = (len(modulated_data.samples) - start_silence_samples - end_silence_samples) / modulated_data.data.getSize()
        for i in range(len(modulated_data.data.getBin())):
            _min = samples_per_byte * i / modulated_data.sample_rate + start_silence
            _max = samples_per_byte * (i + 1) / modulated_data.sample_rate + start_silence
            if modulated_data.data.getBin()[i] == 1:
                plot2.axvspan(xmin=_min, xmax=_max, ymin=-1, ymax=1, alpha=0.3, color='red')
            else:
                plot2.axvspan(xmin=_min, xmax=_max, ymin=-1, ymax=1, alpha=0.1, color='blue')

        plot1.xaxis.set_major_formatter(FormatStrFormatter('%db'))
        plot2.xaxis.set_major_formatter(FormatStrFormatter('%.3fs'))
        plot2.tick_params(axis="x", labelrotation=70)
        plot3.xaxis.set_major_formatter(FormatStrFormatter('%d Hz'))
        plot3.tick_params(axis="x", labelrotation=70)

        plt.suptitle(f"{modulated_data.modulator.__class__.__name__} modulation")
        plt.subplots_adjust(bottom=0.1, top=0.85, left=0.05, right=0.95)

    def modulate(self, input_binary: Binary, modulator_type: type(Modulator)):
        self.logger.debug("pre modulation init")

        modulator = modulator_type(self.logger, self.config, self.comm_config)
        times, samples, sample_rate, class_name = modulator.modulate(input_binary)
        return ModulatedData(class_name, self.config, times, samples, sample_rate, input_binary)

    def play(self, modulated_data: ModulatedData):
        if len(modulated_data.samples) == 0:
            self.logger.error("samples cannot be empty")
            return

        self.logger.info("playing modulated data start")
        sd.play(modulated_data.samples, modulated_data.sample_rate, blocking=True)
        self.logger.info("playing modulated data end")

    def save(self, modulated_data: ModulatedData, filepath):
        self.logger.info(f"saving modulated data to '{filepath}'")
        with wave.open(filepath, 'w') as f:
            f.setnchannels(1)
            f.setframerate(modulated_data.sample_rate)
            f.setsampwidth(2)
            for sample in copy.copy(modulated_data.samples):
                sample = int(sample * (2 ** 15 - 1))
                f.writeframes(struct.pack("<h", sample))

    def encode_data(self, input_binary: Binary):
        config = self.comm_config

        start_bit = config["start_byte"]
        stop_bit = config["stop_byte"]
        packet_len = config["packet_len[bytes]"]
        use_crc = config["crc8_sum"]

        packets = []

        bytes_in_packet = 0
        _packet = []
        for _byte in input_binary.getByteArray():
            _packet.append(_byte)
            bytes_in_packet += 1
            if bytes_in_packet == packet_len:
                packets.append(_packet)
                _packet = []
                bytes_in_packet = 0

        if 0 < bytes_in_packet < packet_len:
            for i in range(packet_len - bytes_in_packet):
                _packet.append(0)
            packets.append(_packet)

        calculator = Calculator(Crc8.CCITT)  # noqa

        for packet in packets:
            bin_packet = Binary(bytearray(packet)).getByteArray()
            if use_crc:
                crc_sum = calculator.checksum(bin_packet)
                packet.append(crc_sum)
            packet.insert(0, start_bit)
            packet.append(stop_bit)

        output = bytearray()
        for packet in packets:
            for data in packet:
                output.append(data)

        return Binary(output)


class DemodulatorHub(HUB):

    def analise_demodulated_data(self, demodulated_data:DemodulatedData):
        self.logger.info("analysing modulated data")

        fig = plt.gcf()
        fig.set_size_inches(17, 8)
        fig.set_dpi(100)

        plot1 = plt.subplot2grid((10, 10), (0, 0), rowspan=3, colspan=7)
        plot1.set_title("audio data")
        plot2 = plt.subplot2grid((10, 10), (4, 0), rowspan=6, colspan=7)
        plot2.set_title("demodulated data")
        plot3 = plt.subplot2grid((10, 10), (0, 8), rowspan=10, colspan=2)
        plot3.set_title("PSD")

        # plot 1
        plot1.plot(demodulated_data.audio.getSamples(), color="blue")

        # plot 2
        height = 1.5
        plot2.step([x for x in range(len(demodulated_data.digital_samples))], demodulated_data.digital_samples, color="black")
        plot2.fill_between([x for x in range(len(demodulated_data.digital_samples))], demodulated_data.digital_samples,
                           step="pre", alpha=1, color='black')
        for point in demodulated_data.bits_analysis:
            plot2.axvspan(point.left_edge, point.right_edge, color="red" if point.value == 1 else "blue", alpha=0.3)
            half_width = point.width/4
            pos = point.left_edge + half_width
            plot2.text(pos, 1.1, str(point.value), fontsize="x-small", fontstretch="extra-condensed")
        plot2.set_ylim(ymin=0, ymax=height)

        # plot 3
        samples = demodulated_data.audio.getSamples()
        sample_rate = demodulated_data.audio.getSampleRate()
        pxx, freq, line = plot3.psd(samples, Fs=sample_rate, return_line=True)
        plot3.xaxis.set_major_formatter(FormatStrFormatter('%d Hz'))
        plot3.tick_params(axis="x", labelrotation=70)
        line_x = line[0].get_xdata()
        line_y = line[0].get_ydata()
        plot3.fill_between(line_x, line_y, [min(line_y) for x in line_y],
                           alpha=0.4, color='blue')
        plot3.set_xlim(xmin=0, xmax=int(sample_rate / 2))
        plot3.set_ylim(ymin=-100, ymax=max(line_y) + 10)

        plt.suptitle(f"{demodulated_data.demodulator.__class__.__name__} demodulation")
        plt.subplots_adjust(bottom=0.1, top=0.85, left=0.05, right=0.95)

    def demodulate(self, audio: Audio, demodulator_type: type(Demodulator)):
        self.logger.debug("pre demodulation init")
        demodulator = demodulator_type(self.logger, self.config, self.comm_config)
        return demodulator.demodulate(audio)

    def save(self, demodulated_data: DemodulatedData, filepath):
        self.logger.info(f"saving demodulated data to '{filepath}'")
        with open(filepath, 'wb') as f:
            f.write(demodulated_data.demodulated_data)


