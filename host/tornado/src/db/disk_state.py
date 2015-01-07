import json
import datetime
import pytz

import boto.dynamodb2.exceptions

from db.db_base import JBoxDB


class JBoxDiskState(JBoxDB):
    NAME = 'jbox_diskstate'
    TABLE = None

    STATE_ATTACHED = 1
    STATE_DETACHED = 0

    def __init__(self, disk_key=None, cluster_id=None, region_id=None, user_id=None, volume_id=None,
                 attach_time=None, create=False):
        if self.table() is None:
            return

        self.item = None
        if create and ((cluster_id is None) or (region_id is None) or (user_id is None)):
            raise AssertionError
        if disk_key is None:
            disk_key = '_'.join([user_id, cluster_id, region_id])
        try:
            self.item = self.table().get_item(disk_key=disk_key)
            self.is_new = False
        except boto.dynamodb2.exceptions.ItemNotFound:
            if create:
                data = {
                    'disk_key': disk_key,
                    'cluster_id': cluster_id,
                    'region_id': region_id,
                    'user_id': user_id
                }

                if volume_id is not None:
                    data['volume_id'] = volume_id
                    if attach_time is None:
                        attach_time = datetime.datetime.now(pytz.utc)
                    data['attach_time'] = JBoxDiskState.datetime_to_epoch_secs(attach_time)

                self.create(data)
                self.item = self.table().get_item(disk_key=disk_key)
                self.is_new = True
            else:
                raise

    def set_attach_time(self, attach_time=None):
        if attach_time is None:
            attach_time = datetime.datetime.now(pytz.utc)
        self.set_attrib('attach_time', JBoxDiskState.datetime_to_epoch_secs(attach_time))

    def get_attach_time(self):
        return JBoxDiskState.epoch_secs_to_datetime(self.item['attach_time'])

    def set_detach_time(self, detach_time=None):
        if detach_time is None:
            detach_time = datetime.datetime.now(pytz.utc)
        self.set_attrib('detach_time', JBoxDiskState.datetime_to_epoch_secs(detach_time))

    def get_detach_time(self):
        return JBoxDiskState.epoch_secs_to_datetime(self.item['detach_time'])

    def get_state(self):
        return self.get_attrib('state')

    def set_state(self, state):
        self.set_attrib('state', state)

    def get_user_id(self):
        return self.get_attrib('user_id')

    def set_user_id(self, user_id):
        self.set_attrib('user_id', user_id)

    def get_region_id(self):
        return self.get_attrib('region_id')

    def set_region_id(self, region_id):
        self.set_attrib('region_id', region_id)

    def get_cluster_id(self):
        return self.get_attrib('cluster_id')

    def set_cluster_id(self, cluster_id):
        self.set_attrib('cluster_id', cluster_id)

    def get_volume_id(self):
        return self.get_attrib('volume_id')

    def set_volume_id(self, volume_id):
        self.set_attrib('volume_id', volume_id)

    def get_snapshot_ids(self):
        snapshots = self.get_attrib('snapshot_id')
        if (snapshots is not None) and (len(snapshots) > 0):
            return json.loads(snapshots)
        return []

    def add_snapshot_id(self, snapshot_id):
        ids = self.get_snapshot_ids()
        ids.append(snapshot_id)
        self.set_snapshot_ids(ids)

    def set_snapshot_ids(self, snapshot_ids):
        self.set_attrib('snapshot_id', json.dumps(snapshot_ids))

    @staticmethod
    def get_detached_disks(max_count=None):
        records = JBoxDiskState.table().query_2(state__eq=JBoxDiskState.STATE_DETACHED,
                                                index='state-index',
                                                limit=max_count)
        disk_keys = []
        for rec in records:
            disk_keys.append(rec['disk_key'])
        return disk_keys
