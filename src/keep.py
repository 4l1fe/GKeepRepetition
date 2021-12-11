import logging
from getpass import getpass

from gkeepapi import Keep as _Keep

from data_layer import Token, State


logger = logging.getLogger()


class Keep(_Keep):

    @staticmethod
    def file_dump(state):
        State.write(state)

    def login(self, email, **kwargs):
        token = Token.read()
        state = State.read()

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
