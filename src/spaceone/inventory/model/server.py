import logging

from schematics import Model
from schematics.types import ModelType, StringType, ListType, DictType, UnionType, IntType, FloatType
from spaceone.inventory.libs.schema.metadata.dynamic_field import TextDyField
from spaceone.inventory.libs.schema.metadata.dynamic_layout import ItemDynamicLayout, ListDynamicLayout
from spaceone.inventory.libs.schema.cloud_service import CloudServiceResource, CloudServiceResponse, CloudServiceMeta

_LOGGER = logging.getLogger(__name__)

'''
ComputeEngine Instance
'''


class MetricDataModel(Model):
    labels = ListType(DictType(IntType), required=True)
    values = ListType(UnionType((FloatType, IntType)), required=True)


class CollectType(Model):
    avg = FloatType(serialize_when_none=False)
    max = FloatType(serialize_when_none=False)


class CPUMonitoring(Model):
    utilization = ModelType(CollectType, serialize_when_none=False)


class MemoryMonitoring(Model):
    usage = ModelType(CollectType, serialize_when_none=False)
    total = ModelType(CollectType, serialize_when_none=False)
    used = ModelType(CollectType, serialize_when_none=False)


class DiskMonitoring(Model):
    write_iops = ModelType(CollectType, serialize_when_none=False)
    write_throughput = ModelType(CollectType, serialize_when_none=False)
    read_iops = ModelType(CollectType, serialize_when_none=False)
    read_throughput = ModelType(CollectType, serialize_when_none=False)


class NetworkCPUMonitoring(Model):
    received_throughput = ModelType(CollectType, serialize_when_none=False)
    received_pps = ModelType(CollectType, serialize_when_none=False)
    sent_throughput = ModelType(CollectType, serialize_when_none=False)
    sent_pps = ModelType(CollectType, serialize_when_none=False)


class Monitoring(Model):
    cpu = ModelType(CPUMonitoring, serialize_when_none=False)
    memory = ModelType(MemoryMonitoring, serialize_when_none=False)
    disk = ModelType(DiskMonitoring, serialize_when_none=False)
    network = ModelType(NetworkCPUMonitoring, serialize_when_none=False)


class Server(Model):
    monitoring = ModelType(Monitoring, default={})
    def reference(self, reference_id):
        return {
            "resource_id": reference_id,
        }


cpu_details_meta = ItemDynamicLayout.set_fields('CPU', fields=[
    TextDyField.data_source('CPU Utilization (Max) | Unit: %', 'data.monitoring.cpu.utilization.max'),
    TextDyField.data_source('CPU Utilization (Avg) | Unit: %', 'data.monitoring.cpu.utilization.avg')
])


memory_details_meta = ItemDynamicLayout.set_fields('Memory', fields=[
    TextDyField.data_source('Memory usage (Max) | Unit: %', 'data.monitoring.memory.usage.max'),
    TextDyField.data_source('Memory usage (Avg) | Unit: %', 'data.monitoring.memory.usage.avg'),
    TextDyField.data_source('Memory Total (Max) | Unit: %', 'data.monitoring.memory.total.max'),
    TextDyField.data_source('Memory Total (Avg) | Unit: %', 'data.monitoring.memory.total.avg'),
    TextDyField.data_source('Memory Used (Max) | Unit: %', 'data.monitoring.memory.used.max'),
    TextDyField.data_source('Memory Used (Avg) | Unit: %', 'data.monitoring.memory.used.avg')
])


disk_details_meta = ItemDynamicLayout.set_fields('Disk', fields=[
    TextDyField.data_source('Disk Write IOPS (Max) | Unit: Counts', 'data.monitoring.disk.write_iops.max'),
    TextDyField.data_source('Disk Write IOPS (Avg) | Unit: Counts', 'data.monitoring.disk.write_iops.avg'),
    TextDyField.data_source('Disk Write Throughput (Max) | Unit: Bytes', 'data.monitoring.disk.write_throughput.max'),
    TextDyField.data_source('Disk Write Throughput (Avg) | Unit: Bytes', 'data.monitoring.disk.write_throughput.avg'),
    TextDyField.data_source('Disk Read IOPS (Max) | Unit: Counts', 'data.monitoring.disk.read_iops.max'),
    TextDyField.data_source('Disk Read IOPS (Avg) | Unit: Counts', 'data.monitoring.disk.read_iops.avg'),
    TextDyField.data_source('Disk Read Throughput (Max) | Unit: Bytes', 'data.monitoring.disk.read_throughput.max'),
    TextDyField.data_source('Disk Read Throughput (Avg) | Unit: Bytes', 'data.monitoring.disk.read_throughput.avg')
])


network_details_meta = ItemDynamicLayout.set_fields('Network', fields=[
    TextDyField.data_source('Network Received Throughput (Max) | Unit: Bytes', 'data.monitoring.network.received_throughput.max'),
    TextDyField.data_source('Network Received Throughput (Avg) | Unit: Bytes', 'data.monitoring.network.received_throughput.avg'),
    TextDyField.data_source('Network Received PPS (Max) | Unit: Counts', 'data.monitoring.network.received_pps.max'),
    TextDyField.data_source('Network Received PPS (Avg) | Unit: Counts', 'data.monitoring.network.received_pps.avg'),
    TextDyField.data_source('Network Sent Throughput (Max) | Unit: Bytes', 'data.monitoring.network.sent_throughput.max'),
    TextDyField.data_source('Network Sent Throughput (Avg) | Unit: Bytes', 'data.monitoring.network.sent_throughput.avg'),
    TextDyField.data_source('Network Sent PPS (Max) | Unit: Counts', 'data.monitoring.network.sent_pps.max'),
    TextDyField.data_source('Network Sent PPS (Avg) | Unit: Counts', 'data.monitoring.network.sent_pps.avg')
])

performance_details = ListDynamicLayout.set_layouts('Performance', layouts=[cpu_details_meta,
                                                                            memory_details_meta,
                                                                            disk_details_meta,
                                                                            network_details_meta])

server_basic_meta = CloudServiceMeta.set_layouts([performance_details])


class ServerInstanceResource(CloudServiceResource):
    provider = StringType(default='aws')
    cloud_service_group = StringType(default='ComputeEngine')
    cloud_service_type = StringType(default='Instance')
    data = ModelType(Server)
    _metadata = ModelType(CloudServiceMeta, default=server_basic_meta, serialized_name='metadata')


class ServerInstanceResponse(CloudServiceResponse):
    match_rules = DictType(ListType(StringType), default={'1': ['reference.resource_id']})
    resource_type = StringType(default='inventory.Server')
    resource = ModelType(ServerInstanceResource)
