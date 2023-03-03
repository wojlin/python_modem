from deeper_code.interfaces import Modulator


class FSK(Modulator):
    def __init__(self, logger):
        print("fsk init")
        self.logger = logger

    def modulate(self, input_binary):
        print("modulating fsk")

        return []
