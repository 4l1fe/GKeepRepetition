from typing import Union

from settings import DATA_DIR


class Token:

    FILE = DATA_DIR / 'token.txt'

    @staticmethod
    def read() -> Union[None, str]:
        if not Token.FILE.exists():
            return None

        with open(Token.FILE.as_posix(), 'r') as file:
            token = file.read()
        return token

    @staticmethod
    def write(token):
        with open(Token.FILE.as_posix(), 'w') as file:
            file.write(token)