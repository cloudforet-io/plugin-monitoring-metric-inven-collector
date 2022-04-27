__all__ = ['CollectorManager']

import concurrent.futures
from spaceone.core.manager import BaseManager
from datetime import datetime, timedelta
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


class CollectorManager(BaseManager):
    provider = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity_mgr = self.locator.get_manager('IdentityManager')
        self.inventory_mgr = self.locator.get_manager('InventoryManager')
        self.monitoring_mgr = self.locator.get_manager('MonitoringManager')
        self.set_time(1)

    def collect_resources(self, identity_endpoint, endpoint_type, metric_schema, domain_id) -> list:
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
                # Assgin each class,
                # since how to efficiently collect data depends on provider
                return self.collect_metric_data(data_source_id, metric_schema, domain_id)

        except Exception as e:
            _LOGGER.error(e)
            return []

    def collect_metric_data(self, data_source_id, metric_schema, domain_id) -> list:
        raise NotImplemented

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
            elif  endpoint['service'] == 'monitoring':
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

    def set_time(self, interval_options: int):
        self.end = datetime.utcnow()
        self.start = self.end - timedelta(days=interval_options)

#    def list_metrics(self, provider, resource_type, server_ids):
#        data_source = self.get_data_source_info_by_provider(provider)
#        metric_list = self.monitoring_manager.get_metric_list(data_source.get('data_source_id'),
#                                                              resource_type,
#                                                              server_ids)
#
#        return metric_list


    def get_servers_metric_data(self, metric_infos, provider, data_source_id, server_ids, start, end, domain_id):
        server_monitoring_vo = {}

        metric_info = metric_infos['json']
        metric_keys = metric_infos['key']

        """
        metric_info:
        {'cpu': {'utilization': {'aws': [{'metric': 'CPUUtilization', 'resource_type': 'inventory.Server'}],
                                'google_cloud': [{'metric': 'compute.googleapis.com/instance/cpu/utilization',
                                            'resource_type': 'inventory.Server'}],
                                'azure': [{'metric': 'Percentage CPU', 'resource_type': 'inventory.Server'}]}}
        ...

        metric_keys:
        ['cpu.utilization', 'memory.usage', 'memory.total', 'memory.used',
        'disk.write_iops', 'disk.write_throughput', 'disk.read_iops', 'disk.read_throughput',
        'network.received_throughput', 'network.received_pps', 'network.sent_throughput', 'network.sent_pps']
        """
        for collect_item in metric_keys:
            temp = collect_item.split('.')
            mon_type = temp[0]      # ex. cpu
            mon_label = temp[1]     # ex. utilization
            if mon_type not in server_monitoring_vo:
                server_monitoring_vo.update({mon_type: {}})

            if provider in metric_info[mon_type][mon_label]:
                for provider_metric in metric_info[mon_type][mon_label][provider]:
                    # ex: [{'metric': 'CPUUtilization', 'resource_type': 'inventory.Server'}]
                    # metric_data contains metric data via index
                    # 0: max (Max)
                    # 1: avg (Average or Mean)

                    metric_data = [{}, {}]

                    if provider_metric.get('metric') != '':
                        param = self._get_metric_param(provider,
                                                       data_source_id,
                                                       'inventory.Server',
                                                       server_ids,
                                                       provider_metric.get('metric'),
                                                       start,
                                                       end)

                        metric_data[0] = self.get_metric_data(param, domain_id)
                        param.update({'stat_flag': 'avg'})
                        metric_data[1] = self.get_metric_data(param, domain_id)

                        vo = server_monitoring_vo[mon_type].get(mon_label)
                        server_monitoring_vo[mon_type].update(
                            {mon_label: self.get_collect_data_per_state(metric_data, server_ids, vo)})
        """
        {'cpu': {'utilization': {'max': {'labels': ['2022-04-26T16:27:00.000Z'],
                'resource_values': {'server-b1dec2d5a73c': [23.95079835994533],
                                    'server-17f2480b4805': [82.48675132486751],
                                    'server-bfba4b29ce3a': [82.04166666666666],
        """
        return server_monitoring_vo

    def get_metric_data(self, params, domain_id):
        stat_flag = 'MAX'

        stat_interval = params.get('stat_interval') if params.get('stat_interval') is not None else DEFAULT_INTERVAL

        if params.get('stat_flag') == 'avg':
            stat_flag = 'AVERAGE' if params.get('provider') == 'aws' else 'MEAN'

        monitoring_data = self.monitoring_mgr.get_metric_data(params.get('data_source_id'),
                                                                  params.get('source_type'),
                                                                  params.get('server_ids'),
                                                                  params.get('metric'),
                                                                  params.get('start'),
                                                                  params.get('end'),
                                                                  domain_id,
                                                                  stat_interval,
                                                                  stat_flag)

        return monitoring_data

    def get_collect_data_per_state(self, metric_data, server_ids, previous_dt):
        collected_data_map = {}
        if len(metric_data) != len(metric_data):
            raise ERROR_NOT_SUPPORT_STAT(supported_stat=' | '.join(COLLECTIVE_STATE))
        for idx, state in enumerate(COLLECTIVE_STATE):
            state_data = metric_data[idx]
            filter_dt = self._get_only_available_values(state_data, server_ids)
            if previous_dt:
                previous_filtered = self._get_only_available_values(previous_dt[state], server_ids)
                if bool(filter_dt.get('resource_values', {})):
                    merge_pre = previous_filtered.get('resource_values', {})
                    merged_aft = filter_dt.get('resource_values', {})
                    resource = {**merge_pre, **merged_aft}
                    collected_data_map.update({
                        state: {'resource_values': resource,
                                'labels': filter_dt.get('labels'),
                                'domain_id': filter_dt.get('domain_id')}
                    })
                else:
                    collected_data_map.update({
                        state: previous_filtered
                    })
            else:
                collected_data_map.update({
                    state: filter_dt
                })

        return collected_data_map

    def set_metric_data_to_server(self, metric_info_vo, servers, collected_data):
        return_list = []
        metric_keys = metric_info_vo.get('key')

        for server in servers:
            server_vo = {}


            provider = server.get('provider')
            server_id = server.get('server_id')

            if collected_data != {}:
                for metric_key in metric_keys:
                    key = metric_key.split('.')
                    mon_type = key[0]      # ex. cpu
                    mon_label = key[1]     # ex. utilization
                    if mon_type not in server_vo and mon_type in collected_data:
                        server_vo.update({mon_type: {}})

                    for state in COLLECTIVE_STATE:
                        if mon_label not in server_vo[mon_type] and mon_label in collected_data[mon_type]:
                            server_vo[mon_type].update({mon_label: {}})

                        if mon_type in collected_data and mon_label in collected_data[mon_type]:
                            resources = collected_data[mon_type][mon_label]

                            if state in resources:
                                # If perfer to deliver raw data from monitoring.
                                # server_vo[key[0]][key[1]].update({state: {
                                #     'labels': resources[state].get('labels', []),
                                #     'values': resources[state].get('resource_values', {}).get(server_id, [])
                                # }})
                                metric_value = self._get_data_only(resources, state, server_id)

                                if metric_value is not None:
                                    _metric_value_revised = float(metric_value) if isinstance(metric_value, str) else metric_value
                                    try:
                                        server_vo[mon_type][mon_label].update({state: round(_metric_value_revised, 1)})
                                    except Exception as e:
                                        raise e

                if provider == 'google_cloud':
                    updated_memory = self._set_memory_usage(server_vo)
                    server_vo['memory'].update(updated_memory)

                monitoring_data = Server({'monitoring': Monitoring(server_vo, strict=False)}, strict=False)

                if self._check_to_update(monitoring_data.to_primitive()):
                    if provider == 'aws':
                        compute_vm_resource = ServerAwsInstanceResource({
                            'provider': provider,
                            'cloud_service_group': server.get('cloud_service_group'),
                            'cloud_service_type': server.get('cloud_service_type'),
                            'data': monitoring_data,
                            'reference': ReferenceModel(monitoring_data.reference(server.get('reference').get('resource_id')))
                        }, strict=False)
                        return_list.append(ServerAwsInstanceResponse({'resource': compute_vm_resource}))
                    elif provider == 'azure':
                        compute_vm_resource = ServerAzureInstanceResource({
                            'provider': provider,
                            'cloud_service_group': server.get('cloud_service_group'),
                            'cloud_service_type': server.get('cloud_service_type'),
                            'data': monitoring_data,
                            'reference': ReferenceModel(
                                monitoring_data.reference(server.get('reference').get('resource_id')))
                        }, strict=False)
                        return_list.append(ServerAzureInstanceResponse({'resource': compute_vm_resource}))
                    elif provider == 'google_cloud':
                        compute_vm_resource = ServerGoogleInstanceResource({
                            'provider': provider,
                            'cloud_service_group': server.get('cloud_service_group'),
                            'cloud_service_type': server.get('cloud_service_type'),
                            'data': monitoring_data,
                            'reference': ReferenceModel(
                                monitoring_data.reference(server.get('reference').get('resource_id')))
                        }, strict=False)
                        return_list.append(ServerGoogleInstanceResponse({'resource': compute_vm_resource}))

        return return_list

    @staticmethod
    def _set_memory_usage(server_vo):
        memory = server_vo.get('memory', {})
        total = memory.get('total', {})
        used = memory.get('used', {})
        usage = {}

        if total != {} and used != {}:
            avg_total = total.get('avg')
            avg_used = used.get('avg')
            max_total = total.get('max')
            max_used = used.get('max')

            if avg_total is not None and avg_used is not None:
                avg_usage = float(avg_used) / float(avg_total) * 100
                usage.update({'avg': round(avg_usage, 1)})

            if max_total is not None and max_used is not None:
                max_usage = float(avg_used) / float(avg_total) * 100
                usage.update({'max': round(max_usage, 1)})

        if usage != {}:
            memory.update({'usage': usage})

        return memory

    @staticmethod
    def _get_data_only(metric_data, state, server_id):

        data_only = None
        resource_values = metric_data[state].get('resource_values', {})
        values = resource_values.get(server_id)

        if values and len(values) > 0:
            data_only = values[0]

        return data_only

    @staticmethod
    def _is_update_able(metric, server_id):
        resource_values = metric.get('resource_values')
        values = resource_values.get(server_id)

        return False if not values or values is None else True

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
    def _get_only_available_values(metric_monitoring_data, server_ids):
        dummy = metric_monitoring_data.copy()

        for server_id in server_ids:
            if 'resource_values' in dummy and dummy['resource_values'].get(server_id) == []:
                dummy['resource_values'].pop(server_id, None)

        metric_monitoring_data.update({
            'resource_values': dummy.get('resource_values', {})
        })

        return metric_monitoring_data

#    @staticmethod
#    def _get_only_available_ids(available_resources, server_ids):
#        _available_resources = []
#        if server_ids:
#            if isinstance(server_ids, list):
#                for server_id in server_ids:
#                    if available_resources.get(server_id):
#                        _available_resources.append(server_id)
#            else:
#                if available_resources.get(server_ids):
#                    _available_resources.append(server_ids)
#
#        return _available_resources
#
#    @staticmethod
#    def get_divided_into_max_count(max_count, divide_targets):
#        return_arr = []
#        for idx, target in enumerate(divide_targets, start=0):
#            return_arr_idx = len(return_arr) - 1
#            if return_arr_idx < 0:
#                return_arr.append([target])
#            else:
#                current_target_length = len(return_arr[return_arr_idx])
#                if current_target_length < max_count:
#                    return_arr[return_arr_idx].append(target)
#                else:
#                    return_arr.append([target])
#        return return_arr
#
#    @staticmethod
#    def _get_total_length(server_ids):
#        length = 0
#        for server_id in server_ids:
#            length = length + len(server_id)
#
#        return length
#
    @staticmethod
    def _check_to_update(monitoring_data):
        return True if monitoring_data.get('monitoring', {}) != {} else False
