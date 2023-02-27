import random


def create_random_text(length: int) -> str:
    return ''.join([chr(random.randint(65, 90)) for _ in range(length)])