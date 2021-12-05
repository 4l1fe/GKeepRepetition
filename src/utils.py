import logging

from deepdiff.model import DiffLevel


logger = logging.getLogger()


def print_note(n):
    logger.info(n.timestamps.created, n.timestamps.edited, n.timestamps.updated, n.id, n.type, n.title, n.text)


def get_root_key(diff: DiffLevel) -> str:
    return diff.path(output_format='list')[0]