from unittest.mock import patch
from contextlib import AbstractContextManager

from utils import node_to_str


class Patch(AbstractContextManager):

    def __enter__(self):
        self.patchers = []
        node_str_mock = patch('gkeepapi.node.Note.__str__', node_to_str)
        self.patchers.append(node_str_mock)

        for p in self.patchers:
            p.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for p in self.patchers:
            p.stop()
