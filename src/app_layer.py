import logging
from datetime import datetime
from typing import Tuple, Iterator, List

from gkeepapi.node import ColorValue, NodeType, Node
from deepdiff import DeepDiff
from deepdiff.helper import NotPresent
from peewee import fn

from utils import get_root_key
from data_layer.keep import Keep
from data_layer.models import Event, EventNormalizedView, database
from constants import EventType, LEAST_UPDATED_COUNT

logger = logging.getLogger()


def find_node(nodes, server_id):
    for node in nodes:
        if node['serverId'] == server_id:
            return node

    raise LookupError('No element')


class SyncApplication:

    def __init__(self, email):
        """Устанавливает соединение, реконструирует состояние, но не синхронизируется."""
        self.keep = Keep()
        self.keep.login(email, sync=False)

    def sync_and_dump(self):
        self.keep.sync()
        state = self.keep.dump()
        self.keep.current_state = state

    def sync_and_get_states(self) -> Tuple[dict, dict]:
        prev_state = self.keep.dump()

        logger.info('Syncing...')
        self.keep.sync()
        logger.info('Synced.')

        cur_state = self.keep.dump()

        return prev_state, cur_state

    def make_events(self, previous_nodes, current_nodes) -> List[Event]:
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
            data = find_node(previous_nodes, server_id) if type_ == EventType.DELETED else find_node(current_nodes,
                                                                                                     server_id)
            event = Event(created=datetime.utcnow(), type=type_, data=data)
            events[server_id] = event

        return list(events.values())

    def create_events(self):
        previous_state, current_state = self.sync_and_get_states()

        events = self.make_events(previous_state['nodes'], current_state['nodes'])

        with database.transaction():
            Event.bulk_create(events)
            self.keep.current_state = current_state

        logger.info('Created %s events.', len(events))

    def find_default_least_updated_iter(self, count: int = LEAST_UPDATED_COUNT) -> Iterator[Node]:
        nodes = self.keep.find(colors=[ColorValue.White], archived=False, pinned=False)
        nodes = sorted(nodes, key=lambda n: n.timestamps.updated)
        for i, node in enumerate(nodes, start=1):
            if i > count:
                break

            if node.type != NodeType.Note:
                logger.info('Node type: %s', node.type)
                continue

            yield node

    def pin_default_least_updated(self, count: int = LEAST_UPDATED_COUNT):
        nodes = self.find_default_least_updated_iter(count=count)
        for node in nodes:
            node.pinned = True

        self.create_events()


class DataApplication:

    def _get_day_groups(self, type_: EventType):
        note_created_date = fn.SUBSTR(EventNormalizedView.note_created, 1, 10).alias('note_created_date')
        groups = EventNormalizedView.select(note_created_date, fn.count()) \
            .where(EventNormalizedView.note_type == 'NOTE', EventNormalizedView.event_type == type_) \
            .group_by(note_created_date) \
            .namedtuples()
        logger.debug(groups)
        return groups

    def get_day_groups_created_notes(self):
        groups = self._get_day_groups(EventType.CREATED)
        return groups

    def get_day_groups_updated_notes(self):
        groups = self._get_day_groups(EventType.UPDATED)
        return groups

    def get_day_groups_deleted_notes(self):
        groups = self._get_day_groups(EventType.DELETED)
        return groups
