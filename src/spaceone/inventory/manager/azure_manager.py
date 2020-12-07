__all__ = ['AzureManager']

import time
from spaceone.inventory.model.server import *
from spaceone.inventory.libs.manager import CollectorManager

_LOGGER = logging.getLogger(__name__)


class AzureManager(CollectorManager):
    provider = 'azure'

    def collect_monitoring_data(self, params):
        print("**  Azure monitoring collecting has started **\n")

        start_time = time.time()
        azure_vm_instances = []
        try:
            server_ids = params.get('server_ids').get(self.provider)
            servers = params.get('servers').get(self.provider)
            if None not in [server_ids, servers]:
                monitoring_data = self.get_servers_metric_data(params.get('metric_schema'),
                                                               self.provider,
                                                               server_ids,
                                                               self.start,
                                                               self.end)

                azure_servers_vos = self.set_metric_data_to_server(params.get('metric_schema'),
                                                                    servers,
                                                                    monitoring_data)

                azure_vm_instances.extend(azure_servers_vos)

        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

        print(f' Azure Monitoring data collecting has Finished in  {time.time() - start_time} Seconds')
        return azure_vm_instances
