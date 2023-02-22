from interfaces import Demodulator


class ASK(Demodulator):
    def __init__(self):
        print("ask init")

    def demodulate(self, input_binary):
        print("demodulating ask")
        return []
