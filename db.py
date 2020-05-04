import atexit
from settings import DATA_DIR

from unqlite import UnQLite


DB = DATA_DIR / 'notes.unqlite'
db = UnQLite(DB.as_posix(), open_database=False)
atexit.register(db.close)


def drop_db():
    db.close()
    DB.unlink()

