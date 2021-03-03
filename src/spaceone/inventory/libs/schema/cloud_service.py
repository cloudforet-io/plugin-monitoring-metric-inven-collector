from schematics import Model
from schematics.types import ListType, StringType, PolyModelType, DictType, ModelType
from .base import BaseMetaData, BaseResponse, MetaDataView, MetaDataViewSubData, ReferenceModel


class CloudServiceMeta(BaseMetaData):
    @classmethod
    def set(cls):
        sub_data = MetaDataViewSubData()
        return cls({'view': MetaDataView({'sub_data': sub_data})})

    @classmethod
    def set_layouts(cls, layouts=[]):
        sub_data = MetaDataViewSubData({'layouts': layouts})
        return cls({'view': MetaDataView({'sub_data': sub_data})})


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
