__all__ = ['GoogleCloudManager']
import time
import logging
from spaceone.inventory.model.server import *
from spaceone.inventory.libs.schema.base import ReferenceModel
from spaceone.inventory.libs.manager import CollectorManager
from pprint import pprint
_LOGGER = logging.getLogger(__name__)
COLLECTIVE_STATE = ['max', 'avg']

class GoogleCloudManager(CollectorManager):
    provider = 'google_cloud'

    def collect_monitoring_data(self, params):
        print("**  Google Cloud monitoring collecting has started **")
        start_time = time.time()
        google_compute_vm_instances = []
        try:
            server_ids = params.get('server_ids', {}).get(self.provider)
            servers = params.get('servers', {}).get(self.provider)
            if None not in [server_ids, servers]:
                monitoring_data = self.get_servers_metric_data(params.get('metric_schema'),
                                                               self.provider,
                                                               server_ids,
                                                               self.start,
                                                               self.end)

                servers_vos = self._set_metric_data_to_server(params.get('metric_schema'),
                                                              servers,
                                                              monitoring_data)

                google_compute_vm_instances.extend(servers_vos)

        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

        print(f' Google Cloud Monitoring data collecting has Finished in  {time.time() - start_time} Seconds')
        return google_compute_vm_instances
