from schematics import Model
from schematics.types import ListType, StringType, PolyModelType, DictType, ModelType
from .base import BaseResponse, ReferenceModel


class CloudServiceResource(Model):
    provider = StringType(serialize_when_none=False)
    cloud_service_type = StringType(serialize_when_none=False)
    cloud_service_group = StringType(serialize_when_none=False)
    data = PolyModelType(Model, default=lambda: {})
    reference = ModelType(ReferenceModel)


class CloudServiceResponse(BaseResponse):
    match_rules = DictType(ListType(StringType), default={
        '1': ['reference.resource_id', 'provider', 'cloud_service_type', 'cloud_service_group']
    })
    options = DictType(StringType(), default={
        'update_mode': 'MERGE'
    })
    resource_type = StringType(default='inventory.CloudService')
    resource = PolyModelType(CloudServiceResource)
