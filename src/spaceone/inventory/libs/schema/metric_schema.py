__all__ = ['MetricSchemaManager']
from spaceone.core.manager import BaseManager
from spaceone.inventory.error.custom import *
from spaceone.inventory.model.metric_schema import *

SUPPORTED_PROVIDERS = ['aws', 'google_cloud', 'azure']

METRIC_SCHEMA = {

'aws': [{"key": "cpu.utilization", "metric": "CPUUtilization"},
               {"key": "disk.write_iops", "metric": "DiskWriteOps"},
               {"key":"disk.write_iops", "metric": "EBSWriteOps"},
               {"key":"disk.write_throughput", "metric": "DiskWriteBytes"},
               {"key":"disk.write_throughput", "metric": "EBSWriteBytes"},
               {"key":"disk.read_iops", "metric": "DiskReadOps"},
               {"key":"disk.read_iops", "metric": "EBSReadOps"},
               {"key":"disk.read_throughput", "metric": "DiskReadBytes"},
               {"key":"disk.read_throughput", "metric": "EBSReadBytes"},
               {"key":"network.received_throughput", "metric": "NetworkIn"},
               {"key":"network.received_pps", "metric": "NetworkPacketsIn"},
               {"key":"network.sent_throughput", "metric": "NetworkOut"},
               {"key":"network.sent_pps", "metric": "NetworkPacketsOut"}],

'google_cloud': [{"key":"cpu.utilization", "metric":"compute.googleapis.com/instance/cpu/utilization"},
                {"key":"memory.total", "metric":"compute.googleapis.com/instance/memory/balloon/ram_size"},
                {"key":"memory.used", "metric":"compute.googleapis.com/instance/memory/balloon/ram_used"},
                {"key":"disk.write_iops", "metric":"compute.googleapis.com/instance/disk/write_ops_count"},
                {"key":"disk.write_throughput", "metric":"compute.googleapis.com/instance/disk/write_bytes_count"},
                {"key":"disk.read_iops", "metric":"compute.googleapis.com/instance/disk/read_ops_count"},
                {"key":"disk.read_throughput", "metric":"compute.googleapis.com/instance/disk/read_bytes_count"},
                {"key":"network.received_throughput", "metric":"compute.googleapis.com/instance/network/received_bytes_count"},
                {"key":"network.received_pps", "metric":"compute.googleapis.com/instance/network/received_packets_count"},
                {"key":"network.sent_throughput", "metric":"compute.googleapis.com/instance/network/sent_bytes_count"},
                {"key":"network.sent_pps", "metric": "compute.googleapis.com/instance/network/sent_packets_count"}],

'azure': [{"key": "cpu.utilization", "metric": "Percentage CPU"},
       {"key": "disk.write_iops", "metric": "Data Disk Write Operations/Sec"},
       {"key": "disk.write_throughput", "metric": "Disk Write Bytes"},
       {"key": "disk.read_iops", "metric": "Disk Read Operations/Sec"},
       {"key": "disk.read_throughput", "metric": "Disk Read Bytes"},
       {"key": "network.received_throughput", "metric": "Network In"},
       {"key": "network.received_pps", "metric": "Inbound Flows"},
       {"key": "network.sent_throughput", "metric": "Network Out"},
       {"key": "network.sent_pps", "metric": "Outbound Flows"}]
}


class MetricSchemaManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.providers = SUPPORTED_PROVIDERS

        try:
            self.schema = MetricSchema()
            for provider in self.providers:
                if provider in METRIC_SCHEMA:
                    self.set_metrics(provider, METRIC_SCHEMA[provider], kwargs.get('resource_type'))

        except Exception as e:
            print()
            raise ERROR_UNKNOWN(message=e)

    def set_metrics(self, provider, metric_list, resource_type):
        for metric in metric_list:
            map_key = metric.get('key').split('.')
            if len(map_key) != 2:
                raise ERROR_NOT_SUPPORT_METRIC_FORMAT(
                    metric_format=f'key: xxxx.xxxx, resource_type: {resource_type}, metric: metric_name')
            else:
                self.schema[map_key[0]][map_key[1]][provider].append({
                    'metric': metric.get('metric'),
                    'resource_type': resource_type,
                })
