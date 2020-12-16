__all__ = ['GoogleCloudManager']
import time
from pprint import pprint

import concurrent.futures
from spaceone.inventory.model.server import *
from spaceone.inventory.libs.manager import CollectorManager
_LOGGER = logging.getLogger(__name__)


class GoogleCloudManager(CollectorManager):
    provider = 'google_cloud'

    def collect_monitoring_data(self, params):
        print("**  Google Cloud monitoring collecting has started **\n")

        start_time = time.time()
        google_compute_vm_instances = []
        try:

            server_ids = params.get('server_ids', {}).get(self.provider)
            servers = params.get('servers', {}).get(self.provider)

            # Check available resources
            resources_checker = self.list_metrics(self.provider, 'inventory.Server', server_ids)
            available_resources = self._get_only_available_ids(resources_checker.get('available_resources', {}),
                                                               server_ids)
            # Apply only server that is available for get_metric
            monitoring_data = self.get_servers_metric_data(params.get('metric_schema'),
                                                           self.provider,
                                                           available_resources,
                                                           self.start,
                                                           self.end) if available_resources else {}

            google_servers_vos = self.set_metric_data_to_server(params.get('metric_schema'),
                                                          servers,
                                                          monitoring_data)


            google_compute_vm_instances.extend(google_servers_vos)

        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

        print(f' Google Cloud Monitoring data collecting has Finished in  {time.time() - start_time} Seconds')
        return google_compute_vm_instances








