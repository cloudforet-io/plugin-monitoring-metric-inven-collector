__all__ = ['AWSManager']

import time
import logging
import concurrent.futures
from datetime import datetime, timedelta

from spaceone.inventory.manager.collector.manager import CollectorManager
from spaceone.inventory.model.server import *

from pprint import pprint

_LOGGER = logging.getLogger(__name__)
NUM_MAX_INSTANCE = 200
NUM_MAX_INSTANCE = 20

METRIC_SCHEMA = {
    'inventory.Server': [
        {"key": "cpu.utilization", "metric": "CPUUtilization"},
        {"key": "disk.write_iops", "metric": "DiskWriteOps"},
        {"key": "disk.write_iops", "metric": "EBSWriteOps"},
        {"key": "disk.write_throughput", "metric": "DiskWriteBytes"},
        {"key": "disk.write_throughput", "metric": "EBSWriteBytes"},
        {"key": "disk.read_iops", "metric": "DiskReadOps"},
        {"key": "disk.read_iops", "metric": "EBSReadOps"},
        {"key": "disk.read_throughput", "metric": "DiskReadBytes"},
        {"key": "disk.read_throughput", "metric": "EBSReadBytes"},
        {"key": "network.received_throughput", "metric": "NetworkIn"},
        {"key": "network.received_pps", "metric": "NetworkPacketsIn"},
        {"key": "network.sent_throughput", "metric": "NetworkOut"},
        {"key": "network.sent_pps", "metric": "NetworkPacketsOut"}
    ],
}


class AWSManager(CollectorManager):
    provider = 'aws'
    # which is collected by default
    default_metrics = [{'resource_type': 'inventory.Server', 'metric': ['cpu.utilization'], 'provider': 'aws'}]


    def list_supported_metrics(self):
        response = []
        result = []
        for key, value in METRIC_SCHEMA.items():
            for item in value:
                result.append(item['key'])
            response.append({'resource_type': key, 'metric': result, 'provider': self.provider})
        return response

    def list_default_metrics(self):
        return self.default_metrics

    def _init_members(self, resource_type, period, data_source_id):
        self.data_source_id = data_source_id
        self.resource_type = resource_type
        self.start = self.end - timedelta(days=period)
        self.period = period

    def _collect_metric_data_per_provider(self, data_source_id, domain_id) -> list:

        self.stat_list = ['AVERAGE', 'MAX']

        # collect EC2
        _LOGGER.debug(f'[AWSManager] collect: {self.supported_period} day')
        self._init_members('inventory.Server', self.supported_period, data_source_id)
        return self._collect_servers()

        # collect RDS

        # ...

    def _collect_servers(self) -> list:

        # collect server metric based on member variables
        servers = self.inventory_mgr.list_servers(self.provider, self.domain_id)
        server_group = self._group_server_by_account(servers['results'])

        for item in self.supported_metrics:
            if item['resource_type'] == 'inventory.Server':
                check_list = item['metric']

        for account, server_list in server_group.items():
            # get metric_list
            _LOGGER.debug(f'[collect_metric_data] account: {account}, {len(server_list)}')
            # get data
            next_idx = 0
            for idx in range(0, len(server_list), NUM_MAX_INSTANCE):
                if (idx + NUM_MAX_INSTANCE) > len(server_list):
                    next_idx = len(server_list)
                else:
                    next_idx = idx + NUM_MAX_INSTANCE
                # if number of servers is larger than NUM_MAX_INSTANCE, request sub list
                _LOGGER.debug(f'idx: {idx}, next_idx: {next_idx}')
                self.resources = self._list_resource_ids(server_list[idx: next_idx])

                # Loop per metric schema

                for metric in METRIC_SCHEMA['inventory.Server']:
                    key = metric['key']                 # ex. cpu.utilization
                    # Check supported_metrics, which is collected or not
                    if key not in check_list:
                        print(f'skip {key}')
                        continue

                    self.metric = metric['metric']
                    for stat in self.stat_list:         # AVERAGE, MAX
                        self.stat = stat
                        self._print_members()
                        metric_data = self._get_metric_data()

                        print(metric_data)
                        self._append_to_servers(key, stat, metric_data)

                for resource_id, resource_data in self.resources_dic.items():
                    compute_vm_resource = ServerAwsInstanceResource({
                        'provider': self.provider,
                        'cloud_service_group': resource_data.get('cloud_service_group'),
                        'cloud_service_type': resource_data.get('cloud_service_type'),
                        'data': resource_data.get('data'),
                        'reference': resource_data.get('reference')
                    }, strict=False)

                    yield ServerAwsInstanceResponse({'resource': compute_vm_resource})

    def _group_server_by_account(self, server_list):
        server_group = {}
        for server in server_list:
            account = self._get_account(server)
            if account:
                servers = server_group.get(account, [])
                servers.append(server)
                server_group[account] = servers
        return server_group

    def _get_account(self, server):
        data = server.get('data', {})
        compute = data.get('compute', {})
        account = compute.get('account', None)
        return account
