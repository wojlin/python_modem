from typing import Sequence, Optional
from dataclasses import dataclass
from threading import Thread

from peer_to_peer.Recorder import Recorder, AudioDevice
@dataclass
class Config:
    user_id: str
    modulation_type: str


class PeerToPeerHub:
    def __init__(self, config:):
        Thread(target=self.__listen).start()

    def __listen(self):
        while True:
            pass


class ConfigCli:
    def __init__(self):
        pass

    def setup_config(self):
        user_id = input("user id:")
        modulation_type = input("modulation type:")

        return Config(user_id=user_id, modulation_type=modulation_type)

def main(argv: Optional[Sequence[str]] = None) -> int:
    config = ConfigCli()
    
    hub = PeerToPeerHub(Config)

    return 0


if __name__ == "__main__":
    exit(main())

