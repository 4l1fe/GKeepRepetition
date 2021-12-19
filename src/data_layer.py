import json
from typing import Union

from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, JSONField

from constants import EventType
from settings import DATA_DIR


DB_FILE = DATA_DIR / 'keep.sqlite'
database = SqliteExtDatabase(DB_FILE.as_posix(),  pragmas={'journal_mode': 'wal'})


class Event(Model):
    created = DateTimeField()
    type = SmallIntegerField(choices=EventType.values())
    data = JSONField()

    class Meta:
        database = database
        table_name = 'events'

    def __str__(self):
        return self.created.isoformat(sep=' ', timespec='seconds'), EventType(self.type).name


def create_tables():
    with database:
        database.create_tables([Event])


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


class State:

    FILE = DATA_DIR / 'state.json'

    @staticmethod
    def read() -> Union[None, dict]:
        if not State.FILE.exists():
            return None

        with open(State.FILE.as_posix(), 'r') as file:
            state = json.load(file)
        return state

    @staticmethod
    def write(state: dict):
        with open(State.FILE.as_posix(), 'w') as file:
            json.dump(state, file)