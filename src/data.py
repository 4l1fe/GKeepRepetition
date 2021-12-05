from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, JSONField

from constants import TYPE_UPDATED, TYPE_CREATED, TYPE_DELETED
from settings import DATA_DIR


DB_FILE = DATA_DIR / 'keep.sqlite'
database = SqliteExtDatabase(DB_FILE.as_posix())


class Event(Model):
    created = DateTimeField()
    type = SmallIntegerField(choices=[TYPE_UPDATED, TYPE_CREATED, TYPE_DELETED])
    data = JSONField()

    class Meta:
        database = database
        table_name = 'events'

    def __str__(self):
        return self.created.isoformat(sep=' ', timespec='seconds'), self.type


def create_tables():
    with database:
        database.create_tables([Event])
