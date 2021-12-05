import json
import logging
from typing import Union
from getpass import getpass

from gkeepapi import Keep as _Keep

from settings import DATA_DIR


logger = logging.getLogger()


class Token:

    FILE = DATA_DIR / 'token'

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


class Keep(_Keep):

    FILE = DATA_DIR / 'state.json'

    @staticmethod
    def file_dump(state):
        with open(Keep.FILE, 'w') as file:
            json.dump(state, file)

    def login(self, email, **kwargs):
        token = Token.read()
        state = None
        if Keep.FILE.exists():
            with open(Keep.FILE, 'r') as file:
                state = json.load(file)

        if token:
            logger.info('Resume.')
            self.resume(email, token, state=state, **kwargs)
            return self

        logger.info('Lo.gin')
        psw = getpass('Password: ')
        super(Keep, self).login(email, psw, state=state, **kwargs)
        token = self.getMasterToken()
        Token.write(token)
        return self
