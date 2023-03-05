from typing import Sequence, Optional
from threading import Thread

class PeerToPeerHub:
    def __init__(self, use_api: bool):
        self.__use_api = use_api
        if not use_api:
            self.__config = self.setup_config()

        Thread(target=self.__listen).start()

    def __listen(self):
        while True:
            pass

    def setup_config(self, config: dict = {}):
        if self.__use_api:
            if "user_id" not in config:
                raise Exception("'user_id' not in config")

            if "modulation_type" not in config:
                raise Exception("'modulation_type' not in config")
            return config

        user_id = input("user id:")
        modulation_type = input("modulation type:")

        return {"user_id": user_id, "modulation_type": modulation_type}


def main(argv: Optional[Sequence[str]] = None) -> int:
    hub = PeerToPeerHub(use_api=False)

    return 0


if __name__ == "__main__":
    exit(main())

