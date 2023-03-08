import logging

from dataclasses import dataclass
from typing import List
import pyaudio
import wave
from copy import copy, deepcopy

from peer_to_peer.utils import Config

@dataclass
class AudioDevice:
    index: int
    device_index: int
    name: str
    channels: int


class AudioManager:
    def __init__(self, logger: logging.Logger, peer_config: dict):

        self.__peer_config = peer_config
        self.__logger = logger

        self.__FORMAT = pyaudio.paInt16
        self.__CHANNELS = 1
        self.__RATE = 44100
        self.__CHUNK = 512
        self.__RECORD_SECONDS = 5

        self.__device_index = 2

        self.__audio = pyaudio.PyAudio()

        self.__selected_audio_output_device: AudioDevice
        self.__selected_audio_input_device: AudioDevice
        self.__stream: pyaudio.Stream

        self.__can_record = False
        self.__recording = False

        self.__chunks = []

    def can_record(self):
        return self.__can_record
    def get_chunks(self):
        return deepcopy(self.__chunks)

    def get_chunk(self, i):
        return copy(self.__chunks[i])

    def delete_first_chunk(self):
        if len(self.__chunks):
            self.__chunks = self.__chunks.pop(0)

    def listen(self):
        while True:
            if self.__can_record:
                chunk = self.__record_chunk()
            else:
                self.__logger.error("recording setup is not configured")

    def __record_chunk(self):
        frames = []

        for i in range(0, int(self.__RATE / self.__CHUNK * self.__RECORD_SECONDS)):
            data = self.__stream.read(self.__CHUNK)
            frames.append(data)

        return [item for sublist in frames for item in sublist]


    def get_audio_input_devices(self) -> List[AudioDevice]:
        audio_devices = []
        info = self.__audio.get_host_api_info_by_index(0)
        devices_amount = info.get('deviceCount')
        for i in range(0, devices_amount):
            channels = self.__audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')
            if channels > 0:
                name = self.__audio.get_device_info_by_host_api_device_index(0, i).get('name')
                audio_devices.append(AudioDevice(index=len(audio_devices), device_index=i, name=name, channels=channels))

        return audio_devices


    def get_audio_output_devices(self) -> List[AudioDevice]:
        audio_devices = []
        info = self.__audio.get_host_api_info_by_index(0)
        devices_amount = info.get('deviceCount')
        for i in range(0, devices_amount):
            channels = self.__audio.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')
            if channels > 0:
                name = self.__audio.get_device_info_by_host_api_device_index(0, i).get('name')
                audio_devices.append(AudioDevice(index=len(audio_devices), device_index=i, name=name, channels=channels))

        return audio_devices

    def __set_audio_output_device(self, audio_device_index: int):
        real_devices = self.get_audio_output_devices()
        found_device = any(real_device.device_index == audio_device_index for real_device in real_devices)
        if not found_device:
            raise ConnectionError("audio device not found")
        self.__selected_audio_output_device = audio_device_index

    def __set_audio_input_device(self, audio_device_index: int):
        real_devices = self.get_audio_input_devices()
        found_device = any(real_device.device_index == audio_device_index for real_device in real_devices)
        if not found_device:
            raise ConnectionError("audio device not found")
        self.__selected_audio_input_device = audio_device_index

    def set_audio_devices(self, input_device_index: int, output_device_index: int):
        self.__set_audio_input_device(input_device_index)
        self.__set_audio_output_device(output_device_index)
        self.__setup_recording()

    def __setup_recording(self):
        self.__stream = self.__audio.open(format=self.__FORMAT,
                                          channels=self.__CHANNELS,
                                          rate=self.__RATE,
                                          input=True,
                                          input_device_index=self.__selected_audio_output_device,
                                          output_device_index=self.__selected_audio_output_device,
                                          frames_per_buffer=self.__CHUNK)
        self.__can_record = True

    def stop_recording(self):
        """
        this method stop's recording audio chunks
        """
        if self.__can_record:
            self.__logger.debug("stopping recording...")
            self.__stream.stop_stream()
            self.__stream.close()
            self.__audio.terminate()
            self.__logger.debug("recording stopped!")
            self.__recording = False
        else:
            self.__logger.error("recording cannot be stopped because it's not running")
