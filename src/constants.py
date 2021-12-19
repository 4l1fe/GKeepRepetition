import enum
from typing import List


class EventType(enum.IntEnum):
    UPDATED = 1
    DELETED = 3
    CREATED = 2

    @staticmethod
    def values() -> List[int]:
        return [m.value for m in EventType]


LEAST_UPDATED_COUNT = 5