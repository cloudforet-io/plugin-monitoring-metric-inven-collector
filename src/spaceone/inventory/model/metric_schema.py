from schematics import Model
from schematics.types import ListType, StringType, ModelType


class MetricModel(Model):
    metric = StringType(default='')
    resource_type = StringType(default='inventory.Server')


class Provider(Model):
    aws = ListType(ModelType(MetricModel), default=[], serialize_when_none=False)
    google_cloud = ListType(ModelType(MetricModel), default=[], serialize_when_none=False)
    azure = ListType(ModelType(MetricModel), default=[], serialize_when_none=False)


class CPUMonitoring(Model):
    utilization = ModelType(Provider, default={})


class MemoryMonitoring(Model):
    usage = ModelType(Provider, default={})
    total = ModelType(Provider, default={})
    used = ModelType(Provider, default={})


class DiskMonitoring(Model):
    write_iops = ModelType(Provider, default={})
    write_throughput = ModelType(Provider, default={})
    read_iops = ModelType(Provider, default={})
    read_throughput = ModelType(Provider, default={})


class NetworkCPUMonitoring(Model):
    received_throughput = ModelType(Provider, default={})
    received_pps = ModelType(Provider, default={})
    sent_throughput = ModelType(Provider, default={})
    sent_pps = ModelType(Provider, default={})


class MetricSchema(Model):
    cpu = ModelType(CPUMonitoring, default={})
    memory = ModelType(MemoryMonitoring, default={})
    disk = ModelType(DiskMonitoring, default={})
    network = ModelType(NetworkCPUMonitoring, default={})
