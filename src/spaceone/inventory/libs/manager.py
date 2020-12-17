__all__ = ['CollectorManager']

import concurrent.futures
from spaceone.core.manager import BaseManager
from datetime import datetime, timedelta
from spaceone.inventory.error.custom import *
from spaceone.inventory.model.server import *
from spaceone.inventory.libs.schema.base import ReferenceModel
from pprint import pprint

_LOGGER = logging.getLogger(__name__)
COLLECTIVE_STATE = ['max', 'avg']
DEFAULT_INTERVAL = 86400
MAX_WORKER = 20
MAX_DIVIDING_COUNT = 30


class CollectorManager(BaseManager):
    provider = None

    def __init__(self, **kwargs):
        super().__init__(transaction=None, config=None)
        secret_data = kwargs.get('secret_data')
        self.data_source = secret_data.get('data_source_info')
        self.end = None
        self.start = None

        try:
            self.max_worker = MAX_WORKER
            self.inventory_manager = secret_data.get('inventory_manager')
            self.monitoring_manager = secret_data.get('monitoring_manager')
            self.domain_id = secret_data.get('domain_id')
            self.set_time(1)

        except Exception as e:
            print()
            raise ERROR_UNKNOWN(message=e)

    def verify(self, secret_data, region_name):
        """
            Check connection
        """
        return ''

    def collect_monitoring_data(self, params) -> list:
        raise NotImplemented

    def collect_resources(self, params) -> list:

        return self.collect_monitoring_data(params)

    def set_time(self, interval_options: int):
        self.end = datetime.utcnow()
        self.start = self.end - timedelta(days=interval_options)

    def list_metrics(self, provider, resource_type, server_ids):
        data_source = self.get_data_source_info_by_provider(provider)
        metric_list = self.monitoring_manager.get_metric_list(data_source.get('data_source_id'),
                                                              resource_type,
                                                              server_ids)

        return metric_list

    def get_data_source_info_by_provider(self, provider):
        data_source = self.data_source.get(provider, [])
        return data_source[0] if len(data_source) > 0 else None

    def get_servers_metric_data(self, metric_info_vo, provider, server_ids, start, end):
        server_monitoring_vo = {}
        metric_info = metric_info_vo.get('json')
        metric_keys = metric_info_vo.get('key')
        data_source = self.get_data_source_info_by_provider(provider)

        if data_source:
            for collect_item in metric_keys:
                dict_key = collect_item.split('.')

                if dict_key[0] not in server_monitoring_vo:
                    server_monitoring_vo.update({dict_key[0]: {}})

                if provider in metric_info[dict_key[0]][dict_key[1]]:
                    for provider_metric in metric_info[dict_key[0]][dict_key[1]][provider]:

                        # metric_data contains metric data via index
                        # 0: max (Max)
                        # 1: avg (Average or Mean)

                        metric_data = [{}, {}]

                        if provider_metric.get('metric') != '':
                            param = self._get_metric_param(provider,
                                                           data_source.get('data_source_id'),
                                                           'inventory.Server',
                                                           server_ids,
                                                           provider_metric.get('metric'),
                                                           start,
                                                           end)

                            metric_data[0] = self.get_metric_data(param)
                            param.update({'stat_flag': 'avg'})
                            metric_data[1] = self.get_metric_data(param)

                            vo = server_monitoring_vo[dict_key[0]].get(dict_key[1])
                            server_monitoring_vo[dict_key[0]].update(
                                {dict_key[1]: self.get_collect_data_per_state(metric_data, server_ids, vo)})

        return server_monitoring_vo

    def get_metric_data(self, params):
        stat_flag = 'MAX'

        stat_interval = params.get('stat_interval') if params.get('stat_interval') is not None else DEFAULT_INTERVAL

        if params.get('stat_flag') == 'avg':
            stat_flag = 'AVERAGE' if params.get('provider') == 'aws' else 'MEAN'

        monitoring_data = self.monitoring_manager.get_metric_data(params.get('data_source_id'),
                                                                  params.get('source_type'),
                                                                  params.get('server_ids'),
                                                                  params.get('metric'),
                                                                  params.get('start'),
                                                                  params.get('end'),
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

                    if key[0] not in server_vo and key[0] in collected_data:
                        server_vo.update({key[0]: {}})

                    for state in COLLECTIVE_STATE:
                        if key[1] not in server_vo[key[0]] and key[1] in collected_data[key[0]]:
                            server_vo[key[0]].update({key[1]: {}})

                        if key[0] in collected_data and key[1] in collected_data[key[0]]:
                            resources = collected_data[key[0]][key[1]]

                            if state in resources:
                                # If perfer to deliver raw data from monitoring.
                                # server_vo[key[0]][key[1]].update({state: {
                                #     'labels': resources[state].get('labels', []),
                                #     'values': resources[state].get('resource_values', {}).get(server_id, [])
                                # }})
                                metric_value = self._get_data_only(resources, state, server_id)

                                if metric_value is not None:
                                    server_vo[key[0]][key[1]].update({state: round(metric_value, 1)})

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

    def collect_monitoring_per_accounts(self, params):
        _account = params.get('account')
        server_ids = self.get_divided_into_max_count(MAX_DIVIDING_COUNT, params.get('server_ids'))
        servers = self.get_divided_into_max_count(MAX_DIVIDING_COUNT, params.get('servers'))
        provider = self.provider.replace('_', ' ').title() if self.provider else ''
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
            future_executors = []
            for idx, account in enumerate(server_ids, start=0):
                print(f"@@@ Processing {provider} account:{_account}  {idx + 1}/{len(server_ids)} @@@ \n")
                _params = params.copy()
                _params.update({
                    'server_ids': account,
                    'servers': servers[idx],
                    'account': account,
                })
                future_executors.append(executor.submit(self.collect_monitoring_per_ids, _params))

            for future in concurrent.futures.as_completed(future_executors):
                for result in future.result():
                    yield result

    def collect_monitoring_per_ids(self, params):
        resources = []
        # Check available resources
        server_ids = params.get('server_ids')
        servers = params.get('servers')

        try:
            resources_check = self.list_metrics(self.provider, 'inventory.Server', server_ids)
            available_resources = self._get_only_available_ids(resources_check.get('available_resources', {}),
                                                               server_ids)

            # Apply only server that is available for get_metric
            monitoring_data = self.get_servers_metric_data(params.get('metric_schema'),
                                                           self.provider,
                                                           available_resources,
                                                           self.start,
                                                           self.end) if available_resources else {}

            azure_servers_vos = self.set_metric_data_to_server(params.get('metric_schema'),
                                                               servers,
                                                               monitoring_data)

            resources.extend(azure_servers_vos)

        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

        return resources

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

    @staticmethod
    def _get_only_available_ids(available_resources, server_ids):
        _available_resources = []
        if server_ids:
            if isinstance(server_ids, list):
                for server_id in server_ids:
                    if available_resources.get(server_id):
                        _available_resources.append(server_id)
            else:
                if available_resources.get(server_ids):
                    _available_resources.append(server_ids)

        return _available_resources

    @staticmethod
    def get_divided_into_max_count(max_count, divide_targets):
        return_arr = []
        for idx, target in enumerate(divide_targets, start=0):
            return_arr_idx = len(return_arr) - 1
            if return_arr_idx < 0:
                return_arr.append([target])
            else:
                current_target_length = len(return_arr[return_arr_idx])
                if current_target_length < max_count:
                    return_arr[return_arr_idx].append(target)
                else:
                    return_arr.append([target])
        return return_arr

    @staticmethod
    def _get_total_length(server_ids):
        length = 0
        for server_id in server_ids:
            length = length + len(server_id)

        return length
