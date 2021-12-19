from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, JSONField
from playhouse.kv import KeyValue

from constants import EventType
from settings import DATA_DIR


DB_FILE = DATA_DIR / 'keep.sqlite'
database = SqliteExtDatabase(DB_FILE.as_posix(),  pragmas={'journal_mode': 'wal'})
states_kv = KeyValue(database=database, table_name='keep_states')


def create_tables():
    with database:
        database.create_tables([Event])


class Event(Model):
    created = DateTimeField()
    type = SmallIntegerField(choices=EventType.values())
    data = JSONField()

    class Meta:
        database = database
        table_name = 'events'

    def __str__(self):
        return self.created.isoformat(sep=' ', timespec='seconds'), EventType(self.type).name


class KVRecordAttribute:

    def __set_name__(self, owner, name):
        print('Set name', name)
        self.key_name = name

    def __get__(self, obj, objtype=None):
        print('Get', self.key_name)
        return states_kv.get(self.key_name, default=dict())

    def __set__(self, obj, value):
        print('Set', self.key_name)
        states_kv[self.key_name] = value


class _States:
    previous = KVRecordAttribute()
    current = KVRecordAttribute()
States = _States()
