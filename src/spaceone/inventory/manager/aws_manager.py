__all__ = ['AWSManager']
import time
import logging
from spaceone.inventory.libs.manager import CollectorManager

_LOGGER = logging.getLogger(__name__)

class AWSManager(CollectorManager):
    provider = 'aws'

    def collect_monitoring_data(self, params):
        print("**  AWS monitoring collecting has started **")
        start_time = time.time()
        ec2_resources = []
        try:
            server_ids = params.get('server_ids').get(self.provider)
            servers = params.get('servers').get(self.provider)
            if None not in [server_ids, servers]:
                monitoring_data = self.get_servers_metric_data(params.get('metric_schema'),
                                                               self.provider,
                                                               server_ids,
                                                               self.start,
                                                               self.end)

                servers_vos = self._set_metric_data_to_server(params.get('metric_schema'),
                                                              servers,
                                                              monitoring_data)

                ec2_resources.extend(servers_vos)

        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

        print(f' AWS Monitoring data collecting has Finished in  {time.time() - start_time} Seconds')
        return ec2_resources