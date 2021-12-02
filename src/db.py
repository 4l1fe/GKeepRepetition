from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, JSONField
from settings import DATA_DIR


DB_FILE = DATA_DIR / 'keep.sqlite'
TYPE_UPDATED = 1
TYPE_CREATED = 2
TYPE_DELETED = 3
database = SqliteExtDatabase(DB_FILE.as_posix())


class Event(Model):
    created = DateTimeField()
    type = SmallIntegerField(choices=[TYPE_UPDATED, TYPE_CREATED, TYPE_DELETED])
    data = JSONField()

    class Meta:
        database = database
        table_name = 'events'


def create_tables():
    with database:
        database.create_tables([Event])
