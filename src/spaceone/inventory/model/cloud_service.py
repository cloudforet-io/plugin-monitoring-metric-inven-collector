import logging

from schematics import Model
from schematics.types import ModelType, StringType, ListType, DictType, UnionType, IntType, FloatType, PolyModelType
from spaceone.inventory.libs.schema.cloud_service import CloudServiceResource, CloudServiceResponse

_LOGGER = logging.getLogger(__name__)


class MetricDataModel(Model):
    labels = ListType(DictType(IntType), required=True)
    values = ListType(UnionType((FloatType, IntType)), required=True)


class CollectType(Model):
    avg = ModelType(MetricDataModel, serialize_when_none=False)
    max = ModelType(MetricDataModel, serialize_when_none=False)


class CPUMonitoring(Model):
    utilization = ModelType(CollectType)


class MemoryMonitoring(Model):
    usage = ModelType(CollectType)
    total = ModelType(CollectType)
    used = ModelType(CollectType)


class DiskMonitoring(Model):
    write_iops = ModelType(CollectType)
    write_throughput = ModelType(CollectType)
    read_iops = ModelType(CollectType)
    read_throughput = ModelType(CollectType)


class NetworkCPUMonitoring(Model):
    received_throughput = ModelType(CollectType)
    received_pps = ModelType(CollectType)
    sent_throughput = ModelType(CollectType)
    sent_pps = ModelType(CollectType)


class Monitoring(Model):
    cpu = ModelType(CPUMonitoring, serialize_when_none=False)
    memory = ModelType(MemoryMonitoring, serialize_when_none=False)
    disk = ModelType(DiskMonitoring, serialize_when_none=False)
    network = ModelType(NetworkCPUMonitoring, serialize_when_none=False)


class CloudService(Model):
    monitoring = ModelType(Monitoring, default={})

    def reference(self, resource_id):
        return {
            "resource_id": resource_id,
        }


class CloudServiceInstanceResource(CloudServiceResource):
    cloud_service_group = StringType(default='ComputeEngine')
    cloud_service_type = StringType(default='Instance')
    data = ModelType(CloudService)


class CloudServiceResponse(CloudServiceResponse):
    match_rules = DictType(ListType(StringType), default={'1': ['reference.resource_id']})
    resource_type = StringType(default='inventory.Server')
    resource = ModelType(CloudServiceInstanceResource)
