from schematics import Model
from schematics.types import ListType, StringType, PolyModelType, DictType


class BaseResponse(Model):
    state = StringType(default='SUCCESS', choices=('SUCCESS', 'FAILURE', 'TIMEOUT'))
    resource_type = StringType(required=True)
    match_rules = DictType(ListType(StringType), default={})
    resource = PolyModelType(Model, default={})


class ReferenceModel(Model):
    class Option:
        serialize_when_none = False

    resource_id = StringType(required=False, serialize_when_none=False)
    external_link = StringType(required=False, serialize_when_none=False)

