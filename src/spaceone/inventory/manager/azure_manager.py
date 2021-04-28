__all__ = ['AzureManager']

import time
import concurrent.futures
from spaceone.inventory.model.server import *
from spaceone.inventory.libs.manager import CollectorManager
from pprint import pprint

_LOGGER = logging.getLogger(__name__)
NUM_MAX_INSTANCE = 200


class AzureManager(CollectorManager):
    provider = 'azure'

    def collect_monitoring_data(self, params):
        print("**  Azure monitoring collecting has started **\n")
        start_time = time.time()

        try:

            azure_server_ids = params.get('server_ids').get(self.provider)
            azure_servers = params.get('servers').get(self.provider)
            azure_accounts = params.get('accounts').get(self.provider)

            for account in azure_accounts:
                print(f'@@@ Processing Azure account : {account} @@@ \n')
                _params = params.copy()
                _params.update({
                    'server_ids': azure_server_ids.get(account, []),
                    'servers': azure_servers.get(account, []),
                    'account': account,
                })

                results = self.collect_azure_monitoring_dt_per_accounts(_params)

                for result in results:
                    yield result

        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

        print(f' Azure Monitoring data collecting has Finished in  {time.time() - start_time} Seconds')

    def collect_azure_monitoring_dt_per_accounts(self, params):
        _account = params.get('account')
        server_id_group = self.get_divided_into_max_count(NUM_MAX_INSTANCE, params.get('server_ids'))
        servers = self.get_divided_into_max_count(NUM_MAX_INSTANCE, params.get('servers'))
        _total_length = self._get_total_length(server_id_group)

        for idx, server_ids in enumerate(server_id_group, start=0):
            print(f'No. {idx + 1}\'s: Azure IDs')
            pprint(server_ids)
            print()

            print(f"@@@ Processing Azure account:{_account}  {len(server_ids)}/{_total_length} @@@ \n")
            _params = params.copy()
            _params.update({'server_ids': server_ids,'servers': servers[idx]})

            results = self.collect_azure_monitoring_per_ids(_params)

            for result in results:
                yield result


    def collect_azure_monitoring_per_ids(self, params):
        azure_instance_resources = []
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

            azure_instance_resources.extend(azure_servers_vos)

        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

        return azure_instance_resources