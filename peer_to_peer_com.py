import curses
import logging
import sys
import time
from typing import Sequence, Optional, List
from curses import wrapper
from peer_to_peer.UI import UI
from threading import Thread, Event

from peer_to_peer.AudioManager import AudioManager, AudioDevice

from peer_to_peer.utils import Config, setup_config, configure_logging, setup_audio_devices, User
import json
import os
from ctypes import *
import uuid

import signal
import sys

class PeerToPeerHub:
    def __init__(self, stdscr: curses.window):

        signal.signal(signal.SIGINT, self.quit_program)
        #signal.pause()

        self.__stdscr = stdscr





        self.__user = None
        self.ui = None
        self.__user_id = None
        self.__modulation_type = None
        self.__logger = configure_logging(logs_path="peer_to_peer_com.log", logs_name="peer to peer")
        self.__peer_config = None
        self.__audio_manager: Optional[AudioManager] = None

        self.__launched_app = False

        self.__threads: Optional[List[Thread]] = []
        self.event = Event()

        self.__messages_to_send = []

    def get_user_id(self):
        return self.__user_id

    def get_logger(self):
        return self.__logger

    def update_verbosity(self, verbose: bool):
        self.__logger.setLevel(logging.DEBUG) if verbose else self.__logger.setLevel(logging.ERROR)
        level = logging.DEBUG if verbose else logging.ERROR
        self.__logger.handlers[0].setLevel(level)

    def update_user_id(self, user_id: str = ""):
        self.__user_id = user_id

    def update_modulation_type(self, modulation_type: str = ""):
        self.__modulation_type = modulation_type

    def update_peer_config(self, peer_config: dict):
        self.__peer_config = peer_config
        ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
        def py_error_handler(filename, line, function, err, fmt):
            pass
        c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
        asound = cdll.LoadLibrary('libasound.so')
        asound.snd_lib_error_set_handler(c_error_handler)
        self.__audio_manager = AudioManager(self.__logger, self.__peer_config)
        return {"status": "done"}

    def get_audio_devices(self) -> dict:
        if self.__audio_manager is None:
            return {"status": "error", "message": "peer config needs to be set first"}

        devices = {"input": {}, "output": {}}
        inputs = self.__audio_manager.get_audio_output_devices()
        outputs = self.__audio_manager.get_audio_input_devices()

        for device in inputs:
            devices["input"][str(device.index)] = {"index": device.index,
                                     "device_index": device.device_index,
                                     "name": device.name,
                                     "channels": device.channels}

        for device in outputs:
            devices["output"][str(device.index)] = {"index": device.index,
                                     "device_index": device.device_index,
                                     "name": device.name,
                                     "channels": device.channels}

        return devices

    def set_audio_devices(self, input_device_id, output_device_id):
        if self.__audio_manager is None:
            return {"status": "error", "message": "peer config needs to be set first"}

        try:
            self.__audio_manager.set_audio_devices(input_device_id, output_device_id)
            return {"status": "done", "message": "inputs and output devices are set"}
        except ConnectionError:
            return {"status": "error", "message": "device does not exist"}

    def start_app(self):
        if self.__launched_app:
            return {"status": "error", "message": "app is already running"}
        if self.__user_id is None:
            return {"status": "error", "message": "user id needs to be set before launching app"}
        if self.__modulation_type is None:
            return {"status": "error", "message": "modulation type needs to be set before launching app"}
        if self.__peer_config is None:
            return {"status": "error", "message": "peer config needs to be set before launching app"}
        if not self.__audio_manager.can_record():
            return {"status": "error", "message": "audio devices needs to be set before launching app"}

        print("launching app...")
        self.__threads.append(Thread(target=self.__record_thread, name="recording thread"))
        self.__threads.append(Thread(target=self.__decode_thread, name="decoding thread"))
        self.__threads.append(Thread(target=self.__transmit_thread, name="transmitting thread"))
        for thread in self.__threads:
            thread.start()

        self.__launched_app = True

        self.__user = User(self.__user_id, True)
        self.__stdscr.clear()
        self.ui = UI(self, self.__stdscr, self.__user)



        return {"status": "done"}

    def __decode_thread(self):
        data_packets = []
        while True:
            if self.event.is_set():
                break
            if self.__audio_manager.get_chunks_length():
                packet = self.__audio_manager.get_chunk(0)
                contain_data = True
                if contain_data:
                    self.ui.add_incoming_message("incoming message")
                    data_packets.append(packet)
                    
                self.__audio_manager.delete_first_chunk()

    def __record_thread(self):
        while True:
            if self.event.is_set():
                break
            self.__audio_manager.listen()

    def __transmit_thread(self):
        while True:
            if self.event.is_set():
                break
            if len(self.__messages_to_send):
                self.ui.chatbuffer_add(self.__messages_to_send[0])
                self.__messages_to_send.pop(0)

    def transmit_message(self, message):
        if message == "/quit":
            self.quit_program()
        else:
            self.__messages_to_send.append(message)


    def quit_program(self, sig = None, frame = None):
        curses.endwin()
        print("closing program")
        for thread in self.__threads:
            print(f"closing '{thread.name}' thread")
            self.event.set()
            thread.join()
        print("ending")
        sys.exit(0)


def main():
    hub = wrapper(PeerToPeerHub)




    automated = True

    if not automated:
        config = setup_config()
        hub.update_user_id(config.user_id)
        hub.update_modulation_type(config.modulation_type)
        hub.update_verbosity(config.verbose)
        hub.update_peer_config(config.peer_config)

        audio_devices = hub.get_audio_devices()
        input_device, output_device = setup_audio_devices(audio_devices)
        hub.set_audio_devices(input_device, output_device)

    else:
        hub.update_user_id("test name")
        hub.update_modulation_type("ASK")
        hub.update_verbosity(True)

        dir_name = '/'.join(os.path.dirname(os.path.realpath(__file__)).split('/'))
        path = f"{dir_name}/configs/peer_to_peer_config.json"
        with open(path) as f:
            peer_config = json.loads(f.read())

        status = hub.update_peer_config(peer_config)
        print(status)

        audio_devices = hub.get_audio_devices()
        input_device = 0
        output_device = 0
        for _, device in audio_devices["input"].items():
            if device["name"] == "default":
                input_device = device["device_index"]

        for _, device in audio_devices["output"].items():
            if device["name"] == "default":
                output_device = device["device_index"]
        hub.get_logger().debug(f"input device: {input_device}      output device: {output_device}")
        status = hub.set_audio_devices(input_device, output_device)
        print(status)

    status = hub.start_app()
    #print(status)

    while True:
        message = hub.ui.wait_input()
        hub.transmit_message(message)


if __name__ == "__main__":
    exit(main())

