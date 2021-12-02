import json
import deepdiff

from getpass import getpass
from typing import Union
from gkeepapi import Keep as _Keep
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


class Keep(_Keep):

    def file_dump(self, state):
        print('dump')
        with open(STATE_FILE, 'w') as file:
            json.dump(state, file)

    def sync(self, *args, **kwargs):
        dump = kwargs.pop('dump', False)

        prev_state = self.dump()
        super().sync(*args, **kwargs)
        print('synced')
        cur_state = self.dump()

        if dump:
            self.file_dump(cur_state)

    def login(self, email, **kwargs):
        token = Token.read()
        state = None
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as file:
                state = json.load(file)

        if token:
            print('resume')
            self.resume(email, token, state=state, **kwargs)
            return self

        print('login')
        psw = getpass('Password: ')
        super(Keep, self).login(email, psw, state=state, **kwargs)
        token = self.getMasterToken()
        Token.write(token)
        return self
