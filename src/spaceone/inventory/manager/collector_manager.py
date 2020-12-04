__all__ = ['CollectorManager']

import time
import logging
import json
from os import path
from spaceone.core.manager import BaseManager
from spaceone.inventory.libs.schema.base import ReferenceModel
from datetime import datetime, timedelta
from spaceone.inventory.error.custom import *
from spaceone.inventory.manager.monitoring.inventory_manager import InventoryManager
from spaceone.inventory.manager.monitoring.monitoring_manager import MonitoringManager
from spaceone.inventory.model.server import *
from pprint import pprint

_LOGGER = logging.getLogger(__name__)
BASE_DIR = path.dirname(path.abspath(__file__))
JSON_DIR = path.join(BASE_DIR, 'monitoring/collector_scheme')
COLLECTIVE_STATE = ['max', 'avg']

class CollectorManager(BaseManager):

    def __init__(self, transaction):
        self.secret = None  # secret info for update meta
        self.inventory_manager = None
        self.monitoring_manager = None
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

        # set Managers and dataSources
        metric_info = self.get_metric_info()

        self.set_managers(params)
        self.get_data_source()

        end = datetime.utcnow()
        start = end - timedelta(days=interval_options)

        try:
            servers = self.inventory_manager.list_servers()
            providers, servers_vo_provider = self._get_metric_ids_per_provider(servers)
            monitoring_data = self.get_servers_metric_data(metric_info,
                                                           providers,
                                                           servers_vo_provider,
                                                           start,
                                                           end)

            servers_vos = self._set_metric_data_to_server(metric_info, servers, monitoring_data)

            resources.extend(servers_vos)

        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

        return resources

    def get_data_source(self):
        if not self.data_source_info:
            data_source = self.monitoring_manager.list_data_source()
            self.data_source_info = self._get_data_source_per_provider(data_source)

    def get_metric_info(self):
        metric_info = {'json': self._get_metric_info(path.join(JSON_DIR, 'metric_info.json'))}
        metric_info.update({'key': self._get_collective_metric_key(metric_info.get('json'))})
        return metric_info

    def get_data_source_info_by_provider(self, provider):
        data_source = self.data_source_info.get(provider, [])
        return data_source[0] if len(data_source) > 0 else None

    def set_managers(self, params):
        #
        inventory_manager: InventoryManager = InventoryManager(params)
        inventory_manager.set_connector()
        monitoring_manager: MonitoringManager = MonitoringManager(params)
        monitoring_manager.set_connector()
        self.inventory_manager = inventory_manager
        self.monitoring_manager = monitoring_manager

    def get_servers_metric_data(self, metric_info_vo, providers, server_ids_vo, start, end):
        server_monitoring_vo = {}
        metric_info = metric_info_vo.get('json')
        metric_keys = metric_info_vo.get('key')


        server_ids_vo = {'aws': ['server-67371e41069f']}
        for provider in providers:
            data_source = self.get_data_source_info_by_provider(provider)
            server_monitoring_vo.update({provider: {}})

            if data_source:
                for collect_item in metric_keys:
                    dict_key = collect_item.split('+')

                    if dict_key[0] not in server_monitoring_vo.get(provider):
                        server_monitoring_vo[provider].update({dict_key[0]: {}})

                    if provider in server_ids_vo:
                        server_ids = server_ids_vo.get(provider)
                        data_source_id = data_source.get('data_source_id')

                        for provider_metric in metric_info[dict_key[0]][dict_key[1]][provider]:
                            metric_data = [{}, {}]
                            if provider_metric.get('metric') != '':
                                param = self._get_metric_param(provider,
                                                               data_source_id,
                                                               'inventory.Server',
                                                               server_ids,
                                                               provider_metric.get('metric'),
                                                               start,
                                                               end)

                                metric_data[0] = self.get_metric_data(param)
                                param.update({'stat_flag': 'avg'})
                                metric_data[1] = self.get_metric_data(param)
                                server_monitoring_vo[provider][dict_key[0]].update({dict_key[1]: self._get_collect_data_per_state(metric_data)})

        return server_monitoring_vo

    def get_metric_data(self, params):
        stat_flag = 'MAX'

        # Default: 86400
        # Sample: 21600

        stat_interval = params.get('stat_interval') if params.get('stat_interval') is not None else 86400

        if params.get('stat_flag') == 'avg':
            stat_flag = 'AVERAGE' if params.get('provider') == 'aws' else 'MEAN'

        return self.monitoring_manager.get_metric_data(params.get('data_source_id'),
                                                       params.get('source_type'),
                                                       params.get('server_ids'),
                                                       params.get('metric'),
                                                       params.get('start'),
                                                       params.get('end'),
                                                       stat_interval,
                                                       stat_flag)

    @staticmethod
    def _set_metric_data_to_server(metric_info_vo, servers, collected_data):
        return_list = []
        metric_keys = metric_info_vo.get('key')

        for server in servers:
            server_vo = {}

            provider = server.get('provider')
            server_id = server.get('server_id')
            for metric_key in metric_keys:
                key = metric_key.split('+')

                if key[0] not in server_vo:
                    server_vo.update({key[0]: {}})

                for state in COLLECTIVE_STATE:
                    if key[1] in collected_data[provider][key[0]]:
                        if key[1] not in server_vo[key[0]]:
                            server_vo[key[0]].update({key[1]: {}})

                        resources = collected_data[provider][key[0]][key[1]]
                        if state in resources:
                            server_vo[key[0]][key[1]].update({state: {
                                'labels': resources[state].get('labels', []),
                                'values': resources[state].get('resource_values', {}).get(server_id, [])
                            }})

            monitoring_data = Server({'monitoring': Monitoring(server_vo, strict=False)}, strict=False)

            compute_vm_resource = ServerInstanceResource({
                'provider': provider,
                'cloud_service_group': server.get('cloud_service_group'),
                'cloud_service_type': server.get('cloud_service_type'),
                'data': monitoring_data,
                'reference': ReferenceModel(monitoring_data.reference(server.get('reference').get('resource_id')))
            })

            return_list.append(ServerInstanceResponse({'resource': compute_vm_resource}))

        return return_list

    @staticmethod
    def _get_metric_ids_per_provider(servers):
        providers = []
        provider_vo = {}

        for server in servers:
            if server.get('provider') in providers:
                provider_vo.get(server.get('provider')).append(server.get('server_id'))
            else:
                provider = server.get('provider')
                providers.append(provider)
                provider_vo.update({
                    provider: [server.get('server_id')]
                })

        return providers, provider_vo

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
    def _get_metric_param(provider, data_source_id, source_type, server_ids, metric, start, end):
        return {
            'provider': provider,
            'data_source_id': data_source_id,
            'source_type': source_type,
            'server_ids': server_ids,
            'metric': metric,
            'start': start,
            'end': end,
        }

    @staticmethod
    def _get_collect_data_per_state(metric_data):
        collected_data_map = {}
        if len(metric_data) != len(metric_data):
            raise ERROR_NOT_SUPPORT_STAT(supported_stat=' | '.join(COLLECTIVE_STATE))

        for idx, state in enumerate(COLLECTIVE_STATE):
            collected_data_map.update({
                state: metric_data[idx]
            })
        return collected_data_map

    @staticmethod
    def _get_metric_info(metric_path):
        with open(metric_path) as json_file:
            json_data = json.load(json_file)
            return json_data

    @staticmethod
    def _get_collective_metric_key(metric_infos):
        metric_keys = []
        for metric_info in metric_infos:
            if isinstance(metric_infos[metric_info], dict):
                for metric in metric_infos[metric_info]:
                    metric_keys.append(f'{metric_info}+{metric}')

        return metric_keys