__all__ = ['CollectorManager']

import concurrent.futures
from datetime import datetime, timedelta
from statistics import mean

from spaceone.core.error import ERROR_NOT_IMPLEMENTED
from spaceone.core.manager import BaseManager
from spaceone.inventory.error.custom import *
from spaceone.inventory.model.server import *
from spaceone.inventory.libs.schema.base import ReferenceModel
from spaceone.inventory.manager.identity_manager import IdentityManager
from spaceone.inventory.manager.inventory_manager import InventoryManager
from spaceone.inventory.manager.monitoring_manager import MonitoringManager
from pprint import pprint

_LOGGER = logging.getLogger(__name__)
COLLECTIVE_STATE = ['max', 'avg']
DEFAULT_INTERVAL = 86400
MAX_WORKER = 20
MAX_DIVIDING_COUNT = 20

def calculate_value_list(stat, value_list):
    if len(value_list) == 0:
        return 0

    if stat == 'AVERAGE':
        return round(mean(value_list), 1)
    elif stat == 'MAX':
        return round(max(value_list), 1)

def merge_new_data(data, key, value):
    """ key: cpu.utilization
        value: {'avg': 1.3}
    """
    item = key.split('.')
    key1 = item[0]  # cpu
    key2 = item[1]  # utilization
    data1 = data.get(key1, {})
    data2 = data1.get(key2, {})
    data2.update(value)
    data1[key2] = data2
    data[key1] = data1
    return data


class CollectorManager(BaseManager):
    provider = None
    default_metrics = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity_mgr = self.locator.get_manager('IdentityManager')
        self.inventory_mgr = self.locator.get_manager('InventoryManager')
        self.monitoring_mgr = self.locator.get_manager('MonitoringManager')
        self.supported_period = 1
        self.data_source_id = None
        self.resource_type = None
        self.resources = []
        self.metric = None
        self.start = None   # will be calculated by supported period
        self.end = datetime.utcnow()
        self.period = None
        self.stat =None
        self.domain_id = None
        self.resources_dic = {}         # dictionary per server_id or cloud_service_id
        self.supported_metrics = {}     # supported_metrics from options

    def list_supported_metrics(self):
        pass

    def list_default_metrics(self):
        pass

    def collect_resources(self, identity_endpoint, endpoint_type, domain_id,
                          supported_metrics, supported_period) -> list:
        # init members
        self.domain_id = domain_id
        self._update_supported_metrics(supported_metrics)
        self.supported_period = int(supported_period)

        try:
            self._update_endpoints(identity_endpoint, endpoint_type, domain_id)

            # find data source
            # WARNING: we assume, there is one proper data_source per provider
            data_source_ids = self._get_data_sources(self.provider, domain_id)
            if len(data_source_ids) == 0:
                _LOGGER.debug(f'There is no data-source, skip this provider: {self.provider}')
                return []

            _LOGGER.debug(f'[collect_resources] provider: {self.provider}, data_source_id: {data_source_ids}')

            for data_source_id in data_source_ids:
                # get metric
                # Assign each class,
                # since how to efficiently collect data depends on provider
                return self._collect_metric_data_per_provider(data_source_id, domain_id)

        except Exception as e:
            _LOGGER.error(e)
            return []

    def _update_supported_metrics(self, metric_list):
        self.supported_metrics = self.default_metrics
        print("XXXX before supported_metrics XXXXX")
        print(self.supported_metrics)

        temp_by_resource_type = {}
        for item in metric_list:
            if item['provider'] != self.provider:
                continue
            resource_type = item['resource_type']
            temp_by_resource_type[resource_type] = item['metric']

        for item in self.supported_metrics:
            resource_type = item['resource_type']
            item['metric'].extend(temp_by_resource_type[resource_type])

        print("XXXX after supported_metrics XXXXX")
        print(self.supported_metrics)


    def _collect_metric_data_per_provider(self, data_source_id, domain_id) -> list:
        # Implement per provider
        raise ERROR_NOT_IMPLEMENTED

    def _update_endpoints(self, identity_endpoint, endpoint_type, domain_id):
        """ update endpoints of
        - inventory
        - monitoring
        """
        endpoints = self.identity_mgr.get_endpoints(identity_endpoint, endpoint_type, domain_id)
        for endpoint in endpoints:
            if endpoint['service'] == 'inventory':
                self.inventory_mgr.init_endpoint(endpoint['endpoint'])
                _LOGGER.debug(f'init inventory endpoint: {endpoint}')
            elif endpoint['service'] == 'monitoring':
                self.monitoring_mgr.init_endpoint(endpoint['endpoint'])
                _LOGGER.debug(f'init monitoring endpoint: {endpoint}')

    def _get_data_sources(self, provider, domain_id):
        """ Find data source by provider
        """
        data_sources = self.monitoring_mgr.get_data_source(provider, domain_id)
        result = []
        for data_source in data_sources:
            result.append(data_source['data_source_id'])
        return result


    def _list_resource_ids(self, resource_vos):
        # list resource_id from resource_vos
        result = []
        for vo in resource_vos:
            server_id = vo.get('server_id', None)
            # Info:
            # update self.resources_dic
            self.resources_dic[server_id] = vo
            result.append(server_id)
        return result

    def _get_metric_data(self):
        # get metric data from self members
        monitoring_data = self.monitoring_mgr.get_metric_data(self.data_source_id,
                                                              self.resource_type,
                                                              self.resources,
                                                              self.metric,
                                                              self.start,
                                                              self.end,
                                                              self.domain_id,
                                                              self.period,
                                                              self.stat)
        return monitoring_data

    def _append_to_servers(self, key, stat, metric_data):
        """
        key: cpu.utilization
        stat: AVERAGE | MAX
        metric_data:
            {'labels': ['2022-05-27T09:05:00.000Z'],
            'resource_values': {
                'server-5dd366b32baf': [3.5999400009999833],
                'server-dfc099d49629': [3.2950549175819597],
                ...
                }, 'domain_id': 'domain-58010aa2e451'}
        """
        for server_id, value_list in metric_data['resource_values'].items():
            value = calculate_value_list(stat, value_list)
            new_data = {}
            if stat == 'AVERAGE':
                new_data = {'avg': value}
            elif stat == 'MAX':
                new_data = {'max': value}

            server_vo = self.resources_dic[server_id]
            data = server_vo.get('data')
            monitoring = data.get('monitoring', {})
            monitoring = merge_new_data(monitoring, key, new_data)
            data['monitoring'] = monitoring
            server_vo['data'] = data
            self.resources_dic[server_id] = server_vo

    def _print_members(self):
        print("provider       : ", self.provider)
        print("data_source_id : ", self.data_source_id)
        print("resource_type  : ", self.resource_type)
        print("resources      : ", self.resources)
        print("metric         : ", self.metric)
        print("start          : ", self.start)
        print("end            : ", self.end)
        print("period         : ", self.period)
        print("stat           : ", self.stat)
        print("domain_id      : ", self.domain_id)

