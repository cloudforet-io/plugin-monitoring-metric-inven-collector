import logging

from schematics import Model
from schematics.types import ModelType, StringType, ListType, DictType, UnionType, IntType, FloatType
from spaceone.inventory.libs.schema.cloud_service import CloudServiceResource, CloudServiceResponse

_LOGGER = logging.getLogger(__name__)

'''
ComputeEngine Instance
'''

class MetricDataModel(Model):
    labels = ListType(DictType(IntType), required=True)
    values = ListType(UnionType((FloatType, IntType)), required=True)


class CollectType(Model):
    avg = ModelType(MetricDataModel, serialize_when_none=False)
    max = ModelType(MetricDataModel, serialize_when_none=False)


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


class ServerInstanceResource(CloudServiceResource):
    provider = StringType(default='aws')
    cloud_service_group = StringType(default='ComputeEngine')
    cloud_service_type = StringType(default='Instance')
    data = ModelType(Server)


class ServerInstanceResponse(CloudServiceResponse):
    match_rules = DictType(ListType(StringType), default={'1': ['reference.resource_id']})
    resource_type = StringType(default='inventory.Server')
    resource = ModelType(ServerInstanceResource)
