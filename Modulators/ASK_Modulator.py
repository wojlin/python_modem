from interfaces import Modulator


class ASK(Modulator):
    def __init__(self):
        print("ask init")

    def modulate(self, input_binary):
        print("modulating ask")
        return []
