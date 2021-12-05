from deepdiff.model import DiffLevel


def print_note(n):
    print(n.timestamps.created, n.timestamps.edited, n.timestamps.updated, n.id, n.type, n.title, n.text)


def get_root_key(diff: DiffLevel) -> str:
    return diff.path(output_format='list')[0]