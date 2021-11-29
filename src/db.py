import atexit
import pickle
import plyvel

from pathlib import Path
from typing import Tuple
from settings import DATA_DIR
from event import Event


DB_FILE = DATA_DIR / 'notes.ldb'
KEY_TEMPLATE = '{event_type}:{iso_date}:{note_id}:{iso_time}'


class DB:

    def __init__(self, filename: str = DB_FILE.as_posix()):
        self.filename = filename
        self.db = self._create_db(self.filename)
        atexit.register(self.db.close)

    def _create_db(self, filename: str):
        db = plyvel.DB(filename, create_if_missing=True)
        return db

    def drop_db(self):
        self.db.close()
        Path(self.filename).unlink()

    def close(self):
        self.db.close()

    def save_events(self, events: Tuple[Event]):
        with self.db.write_batch(transaction=True) as wb:
            for event in events:
                dt = event.created.isoformat(sep='T', timespec='seconds')
                date, time = dt.split('T')
                key = KEY_TEMPLATE.format(event_type=event.type, iso_date=date, note_id=event.data['serverId'],
                                          iso_time=time).encode()
                value = pickle.dumps(event)
                self.db.put(key, value)
