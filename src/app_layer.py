import logging
from datetime import datetime
from typing import Tuple

from deepdiff import DeepDiff
from deepdiff.helper import NotPresent

from data_layer import Event, database
from utils import get_root_key
from keep import Keep
from constants import EventType


logger = logging.getLogger()


def find_node(nodes, server_id):
    for node in nodes:
        if node['serverId'] == server_id:
            return node

    raise LookupError('No element')


class Application:

    def __init__(self, email, sync=False):
        self.keep = Keep()
        self.keep.login(email, sync=sync)

    def sync(self):
        self.keep.sync()
        state = self.keep.dump()
        Keep.file_dump(state)

    def get_states(self) -> tuple:
        prev_state = self.keep.dump()
        logger.info('Syncing...')
        self.keep.sync()
        logger.info('Synced.')
        cur_state = self.keep.dump()

        return prev_state, cur_state

    def make_events(self, previous_nodes, current_nodes) -> Tuple[Event]:
        """Очередность перезаписи элементов словаря событий: обновленные, созданные, удаленные. Удаленные должны
         остаться последними, созданные должны переписать обновленные"""
        logger.info('Compare the previous and current states.')
        diff = DeepDiff(previous_nodes, current_nodes, exclude_regex_paths="\['sortValue'\]", group_by='serverId',
                        view='tree')

        events = dict()
        values_changed = diff.get('values_changed', list())
        logger.debug('values_changed')
        for dlevel in values_changed:
            server_id = get_root_key(dlevel)
            data = find_node(current_nodes, server_id)
            logger.debug(EventType.UPDATED)
            event = Event(created=datetime.utcnow(), type=EventType.UPDATED, data=data)
            events[server_id] = event

        dictionary_item_added = diff.get('dictionary_item_added', list())
        logger.debug('dictionary_item_added')
        for dlevel in dictionary_item_added:
            server_id = get_root_key(dlevel)
            data = find_node(current_nodes, server_id)
            type_ = EventType.UPDATED
            if isinstance(dlevel.t1, NotPresent):
                type_ = EventType.CREATED
            logger.debug(type_)
            event = Event(created=datetime.utcnow(), type=type_, data=data)
            events[server_id] = event

        dictionary_item_removed = diff.get('dictionary_item_removed', list())
        logger.debug('dictionary_item_removed')
        for dlevel in dictionary_item_removed:
            server_id = get_root_key(dlevel)
            type_ = EventType.UPDATED
            if isinstance(dlevel.t2, NotPresent):
                type_ = EventType.DELETED
            logger.debug(type_)
            data = find_node(previous_nodes, server_id) if type_ == EventType.DELETED else find_node(current_nodes, server_id)
            event = Event(created=datetime.utcnow(), type=type_, data=data)
            events[server_id] = event

        return tuple(events.values())

    def create_events(self):
        previous_state, current_state = self.get_states()
        events = self.make_events(previous_state['nodes'], current_state['nodes'])

        with database.transaction():
            Event.bulk_create(events)
            Keep.file_dump(current_state)

        logger.info('Created %s events.', len(events))