from matplotlib import pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.pyplot import figure
import sounddevice as sd
import os
import numpy as np


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
            self.logger.warning(f"'{config_path}' config for {self.processing_mode} {self.processing_type} not found")
        else:
            config = load_config(config_path)

        return config


class ModulatorHub(HUB):

    def analise_modulated_data(self, modulated_data: ModulatedData):
        self.logger.info("analysing modulated data")

        fig = plt.gcf()
        fig.set_size_inches(10, 8)
        fig.set_dpi(100)

        plot1 = plt.subplot2grid((10, 10), (0, 0), rowspan=3, colspan=5)
        plot1.set_title("binary data")
        plot2 = plt.subplot2grid((10, 10), (4, 0), rowspan=6, colspan=5)
        plot2.set_title("modulated data")
        plot3 = plt.subplot2grid((10, 10), (0, 6), rowspan=10, colspan=4)
        plot3.set_title("PSD")

        plot1.step([x for x in range(modulated_data.data.getSize())], modulated_data.data.getBin(), color='red')
        plot2.plot(modulated_data.times, modulated_data.samples)
        pxx, freq, line = plot3.psd(modulated_data.samples, Fs=modulated_data.sample_rate, return_line=True)

        plot1.fill_between([x for x in range(modulated_data.data.getSize())], modulated_data.data.getBin(), step="pre", alpha=1, color='red')
        plot1.set_xlim(xmin=0, xmax=modulated_data.data.getSize()-1)
        plot1.xaxis.set_ticks(np.arange(0, modulated_data.data.getSize(), 10))
        plot1.set_ylim(ymin=-0.2, ymax=1.2)
        plot1.set_yticks([0, 1])

        plot2.set_xlim(xmin=0, xmax=modulated_data.times[-1])

        plot3.set_xlim(xmin=0, xmax=int(modulated_data.sample_rate/2))
        print(line)
        print(dir(line))
        print()
        for x in line:
            print(x)
        print(line[0])
        print(dir(line[0]))
        line_x = line[0].get_xdata()
        line_y = line[0].get_ydata()
        plot3.fill_between(line_x, line_y, [min(line_y) for x in line_y],
                           alpha=1, color='blue')

        samples_per_byte = len(modulated_data.samples) / modulated_data.data.getSize()
        for i in range(len(modulated_data.data.getBin())):
            print(modulated_data.data.getBin()[i])
            if modulated_data.data.getBin()[i] == 1:
                print(samples_per_byte*i, samples_per_byte*(i+1))
                plot2.axvspan(xmin=int(samples_per_byte*i), xmax=int(samples_per_byte*(i+1)), ymin=-1, ymax=1, alpha=0.5, color='red')
                pass

        plot1.xaxis.set_major_formatter(FormatStrFormatter('%db'))
        plot2.xaxis.set_major_formatter(FormatStrFormatter('%d sample'))
        plot3.xaxis.set_major_formatter(FormatStrFormatter('%d Hz'))

        plt.suptitle(f"{modulated_data.modulator} modulation")
        plt.subplots_adjust(bottom=0.1, top=0.85, left=0.05, right=0.95)
        plt.show()
        plt.clf()

    def modulate(self, input_binary: Binary, modulator_type: type(Modulator)):
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