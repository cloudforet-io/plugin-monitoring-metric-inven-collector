__all__ = ['CollectorManager']

import time
import logging
import json
from os import path
from spaceone.core.manager import BaseManager
from spaceone.core.transaction import Transaction
from datetime import datetime, timedelta
from spaceone.inventory.manager.monitoring.inventory_manager import InventoryManager
from spaceone.inventory.manager.monitoring.monitoring_manager import MonitoringManager
from pprint import pprint

_LOGGER = logging.getLogger(__name__)
BASE_DIR = path.dirname(path.abspath(__file__))
JSON_DIR = path.join(BASE_DIR, 'monitoring/collector_scheme')

class CollectorManager(BaseManager):

    def __init__(self, transaction):
        self.secret = None  # secret info for update meta
        self.data_source_info = None
        super().__init__(transaction)

    def verify(self, secret_data, region_name):
        """
            Check connection
        """
        return ''

    def list_resources(self, params):
        resources = []
        interval_options = 1
        if params.get('interval'):
            interval_options = params.get('interval')

        inventory_manager: InventoryManager = InventoryManager(params)
        inventory_manager.set_connector()

        monitoring_manager: MonitoringManager = MonitoringManager(params)
        monitoring_manager.set_connector()

        end = datetime.utcnow()
        start = end - timedelta(days=interval_options)

        try:

            servers = inventory_manager.list_servers()
            for server in servers:
                provider = server.get('provider')
                self.get_data_source(monitoring_manager)
                # print('server')
                # pprint(server)
                # print()

                if provider == 'aws':
                    pass


                elif provider == 'google_cloud':
                    pass


                elif provider == 'azure':
                    pass


            # cloud_services = inventory_manager.list_cloud_services()
            # resources.extend(cloud_services)
            #
            #
            #
            #
            # print(data_source_infos)

            list_data = monitoring_manager.get_metric_data('ds-e2f992b7c537',
                                                           'inventory.Server',
                                                           'server-29375b721b2b',
                                                           'CPUUtilization',
                                                           start,
                                                           end,
                                                           None,
                                                           'MAX'
                                                           )
            print(list_data)

        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

        return []

    def get_data_source(self, monitoring_manager):
        if not self.data_source_info:
            data_source = monitoring_manager.list_data_source()
            self.data_source_info = self._get_data_source_per_provider(data_source)

    @staticmethod
    def _get_data_source_per_provider(data_sources):
        data_source_infos = {}

        for data_vo in data_sources:
            provider = data_vo.get('provider')
            source_info = {'name': data_vo.get('name'), 'data_source_id': data_vo.get('data_source_id')}
            if provider in data_sources:
                source_ref = data_source_infos.get(provider)
                source_ref.append(source_info)
            else:
                data_source_infos.update({provider: [source_info]})

        return data_source_infos

    @staticmethod
    def _get_metric_info(metric_path):
        with open(metric_path) as json_file:
            json_data = json.load(json_file)
            return json_data