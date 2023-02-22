import json


def load_config(filepath: str) -> dict:
    with open(filepath) as f:
        return json.loads(f.read())








