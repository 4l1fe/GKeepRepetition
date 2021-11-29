import enum

from datetime import datetime
from dataclasses import dataclass


class EventType(enum.IntEnum):
    UPDATED = 1
    CREATED = 2
    DELETED = 3


@dataclass
class Event:
    created: datetime
    type: EventType
    data: dict
