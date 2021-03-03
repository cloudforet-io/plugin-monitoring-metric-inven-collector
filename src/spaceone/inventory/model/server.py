import logging

from schematics import Model
from schematics.types import ModelType, StringType, ListType, DictType, UnionType, IntType, FloatType
from spaceone.inventory.libs.schema.metadata.dynamic_field import TextDyField, SizeField
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
    TextDyField.data_source('CPU Utilization (%) | Avg', 'data.monitoring.cpu.utilization.avg'),
    TextDyField.data_source('CPU Utilization (%) | Max', 'data.monitoring.cpu.utilization.max')
])

memory_details_meta = ItemDynamicLayout.set_fields('Memory', fields=[
    TextDyField.data_source('Memory Usage (%) | Avg', 'data.monitoring.memory.usage.avg'),
    SizeField.data_source('Memory Total | Avg', 'data.monitoring.memory.total.avg'),
    SizeField.data_source('Memory Used  | Avg', 'data.monitoring.memory.used.avg'),
    TextDyField.data_source('Memory Usage (%) | Max', 'data.monitoring.memory.usage.max'),
    SizeField.data_source('Memory Total | Max', 'data.monitoring.memory.total.max'),
    SizeField.data_source('Memory Used  | Max', 'data.monitoring.memory.used.max'),
])

disk_details_meta = ItemDynamicLayout.set_fields('Disk', fields=[
    TextDyField.data_source('Disk Read IOPS | Avg', 'data.monitoring.disk.read_iops.avg'),
    TextDyField.data_source('Disk Write IOPS | Avg', 'data.monitoring.disk.write_iops.avg'),
    SizeField.data_source('Disk Read Throughput | Avg', 'data.monitoring.disk.read_throughput.avg'),
    SizeField.data_source('Disk Write Throughput | Avg', 'data.monitoring.disk.write_throughput.avg'),
    TextDyField.data_source('Disk Read IOPS | Max', 'data.monitoring.disk.read_iops.max'),
    TextDyField.data_source('Disk Write IOPS | Max', 'data.monitoring.disk.write_iops.max'),
    SizeField.data_source('Disk Read Throughput | Max', 'data.monitoring.disk.read_throughput.max'),
    SizeField.data_source('Disk Write Throughput | Max', 'data.monitoring.disk.write_throughput.max'),
])

network_details_meta = ItemDynamicLayout.set_fields('Network', fields=[
    TextDyField.data_source('Network Received PPS | Avg', 'data.monitoring.network.received_pps.avg'),
    TextDyField.data_source('Network Sent PPS | Avg', 'data.monitoring.network.sent_pps.avg'),
    SizeField.data_source('Network Received Throughput | Avg', 'data.monitoring.network.received_throughput.avg'),
    SizeField.data_source('Network Sent Throughput | Avg', 'data.monitoring.network.sent_throughput.avg'),
    TextDyField.data_source('Network Received PPS | Max', 'data.monitoring.network.received_pps.max'),
    TextDyField.data_source('Network Sent PPS | Max', 'data.monitoring.network.sent_pps.max'),
    SizeField.data_source('Network Received Throughput | Max', 'data.monitoring.network.received_throughput.max'),
    SizeField.data_source('Network Sent Throughput | Max', 'data.monitoring.network.sent_throughput.max'),
])

performance_form_1_details = ListDynamicLayout.set_layouts('Performance', layouts=[cpu_details_meta,
                                                                                   disk_details_meta,
                                                                                   network_details_meta])

performance_form_2_details = ListDynamicLayout.set_layouts('Performance', layouts=[cpu_details_meta,
                                                                                   memory_details_meta,
                                                                                   disk_details_meta,
                                                                                   network_details_meta])

server_basic_aws_meta = CloudServiceMeta.set_layouts([performance_form_1_details])
server_basic_azure_meta = CloudServiceMeta.set_layouts([performance_form_1_details])
server_basic_google_meta = CloudServiceMeta.set_layouts([performance_form_2_details])


class ServerAwsInstanceResource(CloudServiceResource):
    provider = StringType(default='aws')
    cloud_service_group = StringType(default='ComputeEngine')
    cloud_service_type = StringType(default='Instance')
    data = ModelType(Server)
    _metadata = ModelType(CloudServiceMeta, default=server_basic_aws_meta, serialized_name='metadata')


class ServerAzureInstanceResource(CloudServiceResource):
    provider = StringType(default='aws')
    cloud_service_group = StringType(default='ComputeEngine')
    cloud_service_type = StringType(default='Instance')
    data = ModelType(Server)
    _metadata = ModelType(CloudServiceMeta, default=server_basic_azure_meta, serialized_name='metadata')


class ServerGoogleInstanceResource(CloudServiceResource):
    provider = StringType(default='aws')
    cloud_service_group = StringType(default='ComputeEngine')
    cloud_service_type = StringType(default='Instance')
    data = ModelType(Server)
    _metadata = ModelType(CloudServiceMeta, default=server_basic_google_meta, serialized_name='metadata')


class ServerAwsInstanceResponse(CloudServiceResponse):
    match_rules = DictType(ListType(StringType), default={'1': ['reference.resource_id']})
    resource_type = StringType(default='inventory.Server')
    resource = ModelType(ServerAwsInstanceResource)


class ServerAzureInstanceResponse(CloudServiceResponse):
    match_rules = DictType(ListType(StringType), default={'1': ['reference.resource_id']})
    resource_type = StringType(default='inventory.Server')
    resource = ModelType(ServerAzureInstanceResource)


class ServerGoogleInstanceResponse(CloudServiceResponse):
    match_rules = DictType(ListType(StringType), default={'1': ['reference.resource_id']})
    resource_type = StringType(default='inventory.Server')
    resource = ModelType(ServerGoogleInstanceResource)
