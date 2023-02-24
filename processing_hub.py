from matplotlib.ticker import FormatStrFormatter
from matplotlib import pyplot as plt
import sounddevice as sd
import numpy as np
import struct
import copy
import wave
import os

from interfaces import Modulator, Demodulator
from utils import load_config, Binary, ModulatedData


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

        samples_per_byte = len(modulated_data.samples) / modulated_data.data.getSize()
        for i in range(len(modulated_data.data.getBin())):
            _min = samples_per_byte * i / modulated_data.sample_rate
            _max = samples_per_byte * (i + 1) / modulated_data.sample_rate
            if modulated_data.data.getBin()[i] == 1:
                plot2.axvspan(xmin=_min, xmax=_max, ymin=-1, ymax=1, alpha=0.3, color='red')
            else:
                plot2.axvspan(xmin=_min, xmax=_max, ymin=-1, ymax=1, alpha=0.1, color='blue')

        plot1.xaxis.set_major_formatter(FormatStrFormatter('%db'))
        plot2.xaxis.set_major_formatter(FormatStrFormatter('%.3fs'))
        plot2.tick_params(axis="x", labelrotation=70)
        plot3.xaxis.set_major_formatter(FormatStrFormatter('%d Hz'))
        plot3.tick_params(axis="x", labelrotation=70)

        plt.suptitle(f"{modulated_data.modulator} modulation")
        plt.subplots_adjust(bottom=0.1, top=0.85, left=0.05, right=0.95)
        plt.show()
        plt.clf()

    def modulate(self, input_binary: Binary, modulator_type: type(Modulator)):
        self.logger.debug("pre modulation init")

        modulator = modulator_type(self.logger, self.config)
        times, samples, sample_rate, class_name = modulator.modulate(input_binary)
        return ModulatedData(class_name, times, samples, sample_rate, input_binary)

    def play(self, modulated_data: ModulatedData):
        if len(modulated_data.samples) == 0:
            self.logger.error("samples cannot be empty")
            return

        self.logger.info("playing modulated data start")
        sd.play(modulated_data.samples, modulated_data.sample_rate)
        self.logger.info("playing modulated data end")

    def save(self, modulated_data: ModulatedData, filepath):
        self.logger.info(f"saving modulated data to {filepath}")
        with wave.open(filepath, 'w') as f:
            f.setnchannels(1)
            f.setframerate(modulated_data.sample_rate)
            f.setsampwidth(2)
            for sample in copy.copy(modulated_data.samples):
                sample = int(sample * (2 ** 15 - 1))
                f.writeframes(struct.pack("<h", sample))

    def encode_data(self, input_binary: Binary):
        config = load_config("configs/communication_config.json")

        output = bytearray()
        return input_binary


class DemodulatorHub(HUB):

    def demodulate(self, input_samples: list, modulator_type: type(Demodulator)):
        self.logger.debug("pre demodulation init")
