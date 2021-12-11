from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, JSONField

from constants import EventType
from settings import DATA_DIR


DB_FILE = DATA_DIR / 'keep.sqlite'
database = SqliteExtDatabase(DB_FILE.as_posix())


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
