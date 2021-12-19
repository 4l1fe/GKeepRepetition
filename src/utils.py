import logging

from deepdiff.model import DiffLevel
from gkeepapi.node import Note

from constants import EventType


logger = logging.getLogger()


def print_note(n):
    logger.info(n.timestamps.created, n.timestamps.edited, n.timestamps.updated, n.id, EventType(n.type).name, n.title,
                n.text)


def get_root_key(diff: DiffLevel) -> str:
    return diff.path(output_format='list')[0]


def node_to_str(self: Note):
    created = self.timestamps.created.isoformat(sep=' ', timespec='seconds')
    updated = self.timestamps.updated.isoformat(sep=' ', timespec='seconds')
    return f'Node<{self.type.value}, "{self.title}", "{self.text}", created="{created}", updated="{updated}">'
