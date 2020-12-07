import time
import logging
import json
import concurrent.futures
from spaceone.core.service import *
from pprint import pprint
from spaceone.inventory.libs.schema.metric_schema import MetricSchemaManager
from spaceone.inventory.manager.monitoring.identity_manager import IdentityManager
from spaceone.inventory.manager.monitoring.inventory_manager import InventoryManager
from spaceone.inventory.manager.monitoring.monitoring_manager import MonitoringManager

_LOGGER = logging.getLogger(__name__)
MAX_WORKER = 20
SUPPORTED_RESOURCE_TYPE = ['inventory.Server', 'inventory.CloudService']
FILTER_FORMAT = []


@authentication_handler
class CollectorService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.metric_schema: MetricSchemaManager = MetricSchemaManager(resource_type='inventory.Server')
        self.execute_managers = [
            'AWSManager',
            'AzureManager',
            'GoogleCloudManager'
        ]

    @check_required(['options'])
    def init(self, params):
        """ init plugin by options
        """
        capability = {
            'filter_format': FILTER_FORMAT,
            'supported_resource_type': SUPPORTED_RESOURCE_TYPE
        }
        return {'metadata': capability}

    @transaction
    @check_required(['options', 'secret_data'])
    def verify(self, params):
        """
        Args:
              params:
                - options
                - secret_data
        """
        options = params['options']
        secret_data = params.get('secret_data', {})

        return {}

    @transaction
    @check_required(['options', 'secret_data', 'filter'])
    def list_resources(self, params):
        """
        Args:
            params:
                - options
                - schema
                - secret_data
                - filter
        """

        start_time = time.time()
        print("[ EXECUTOR START: Monitoring Metric Collector ]")

        # Provide metric_schema what to collect for metric collector in params
        params.update({'metric_schema': self.get_metric_info()})

        secret_data = params.get('secret_data')
        svc_endpoint, domain_id = self._get_end_points(secret_data)
        collector_resource = {'end_point_list': svc_endpoint,
                              'domain_id': domain_id,
                              'api_key': secret_data.get('api_key')}

        inventory_manager, monitoring_manager = self._get_managers(collector_resource)
        data_source_info = self.get_data_source(monitoring_manager)
        collector_resource.update({'inventory_manager': inventory_manager,
                                   'monitoring_manager': monitoring_manager,
                                   'data_source_info': data_source_info
                                   })

        all_servers_list = inventory_manager.list_servers(None)
        providers, server_ids, servers = self._get_metric_ids_per_provider(all_servers_list)

        # providers, server_ids, servers, accounts = self._get_resource_params_per_provider_and_account(all_servers_list)

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
            future_executors = []
            for execute_manager in self.execute_managers:
                print(f'@@@ {execute_manager} @@@ \n')
                _manager = self.locator.get_manager(execute_manager, secret_data=collector_resource)
                if _manager.provider in providers:
                    params.update({'server_ids': server_ids, 'servers': servers})
                    future_executors.append(executor.submit(_manager.collect_resources, params))

            for future in concurrent.futures.as_completed(future_executors):
                for result in future.result():
                    yield result.to_primitive()

        print(f'TOTAL TIME : {time.time() - start_time} Seconds')

    def get_data_source(self, monitoring_manager):
        data_source = monitoring_manager.list_data_source()
        return self._get_data_source_per_provider(data_source)

    def get_metric_info(self):
        metric_info = {'json': self.metric_schema.schema.to_primitive()}
        metric_info.update({'key': self._get_collective_metric_key(metric_info.get('json'))})
        return metric_info

    @staticmethod
    def _get_end_points(secret_data):
        identity_manager: IdentityManager = IdentityManager(secret_data=secret_data)
        return identity_manager.list_endpoints(), identity_manager.domain_id

    @staticmethod
    def _get_managers(secret_data):
        inventory_manager: InventoryManager = InventoryManager(secret_data=secret_data)
        monitoring_manager: MonitoringManager = MonitoringManager(secret_data=secret_data)

        return inventory_manager, monitoring_manager

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
    def _get_metric_ids_per_provider(servers):
        providers = []
        provider_vo = {}
        servers_vo = {}

        for server in servers:
            if server.get('provider') in providers:
                provider_vo.get(server.get('provider')).append(server.get('server_id'))
                servers_vo.get(server.get('provider')).append(server)
            else:
                provider = server.get('provider')
                providers.append(provider)
                provider_vo.update({
                    provider: [server.get('server_id')]
                })
                servers_vo.update({
                    provider: [server]
                })

        return providers, provider_vo, servers_vo

    @staticmethod
    def _get_resource_params_per_provider_and_account(servers):

        providers = []
        account_vo = {}
        server_id_vo = {}
        servers_vo = {}

        for server in servers:
            account = server.get('data', {}).get('compute', {}).get('account')
            provider = server.get('provider')

            if provider in providers:
                if account in server_id_vo.get(provider):
                    server_id_vo.get(provider)[account].append(server.get('server_id'))
                    servers_vo.get(provider)[account].append(server)
                else:
                    if account not in account_vo.get(provider):
                        account_vo.get(provider).append(account)
                    server_id_vo.get(provider).update({
                        account: [server.get('server_id')]}
                    )
                    servers_vo.get(provider).update({
                        account: [server]}
                    )
            else:
                providers.append(provider)
                account_vo.update({ provider: [account] })
                server_id_vo.update({
                    provider: {
                        account: [server.get('server_id')]
                    }
                })
                servers_vo.update({
                    provider: {
                        account: [server]
                    }
                })

        return providers, server_id_vo, servers_vo, account_vo




    @staticmethod
    def _get_collective_metric_key(metric_infos):
        metric_keys = []
        for metric_info in metric_infos:
            if isinstance(metric_infos[metric_info], dict):
                for metric in metric_infos[metric_info]:
                    metric_keys.append(f'{metric_info}.{metric}')

        return metric_keys
