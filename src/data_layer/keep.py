import logging
from getpass import getpass

from gkeepapi import Keep as _Keep

from data_layer.models import States
from data_layer.token import Token

logger = logging.getLogger()


class Keep(_Keep):

    @property
    def previous_state(self):
        return States.previous

    @previous_state.setter
    def previous_state(self, value):
        States.previous = value

    @property
    def current_state(self):
        return States.current

    @current_state.setter
    def current_state(self, value):
        States.current = value

    def login(self, email, **kwargs):
        token = Token.read()

        if token:
            logger.info('Resume.')
            self.resume(email, token, state=self.current_state, **kwargs)
            return self

        logger.info('Login')
        psw = getpass('Password: ')
        super().login(email, psw, state=self.current_state, **kwargs)
        token = self.getMasterToken()
        Token.write(token)
        return self
