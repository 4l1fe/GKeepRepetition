import json

from getpass import getpass
from typing import Union
from gkeepapi import Keep
from settings import DATA_DIR


STATE_FILE = DATA_DIR / 'state.json'


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


class Keeep(Keep):

    def sync(self, *args, **kwargs):
        dump = kwargs.pop('dump', False)
        super().sync(*args, **kwargs)
        print('synced')
        state = self.dump()

        if dump:
            print('dump')
            with open(STATE_FILE, 'w') as file:
                json.dump(state, file)

    def login(self, email, *args, **kwargs):
        token = Token.read()
        state = None
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as file:
                state = json.load(file)

        # email = input('Email: ')
        if token:
            print('resume')
            self.resume(email, token, state=state)
            return self

        print('login')
        psw = getpass('Password: ')
        super(Keeep, self).login(email, psw, *args, state=state, **kwargs)
        token = self.getMasterToken()
        Token.write(token)
        return self
