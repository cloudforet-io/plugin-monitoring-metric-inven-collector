import logging

from google.protobuf.json_format import MessageToDict

from spaceone.core.connector import BaseConnector
from spaceone.core import pygrpc
from spaceone.core.utils import parse_grpc_endpoint
from spaceone.core.error import *

__all__ = ['IdentityConnector']

_LOGGER = logging.getLogger(__name__)


class IdentityConnector(BaseConnector):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        e = parse_grpc_endpoint(self.endpoint)
        self.client = pygrpc.client(endpoint=e['endpoint'], ssl_enabled=e['ssl_enabled'])

    def get_end_points(self, domain_id, endpoint_type='internal'):
        response = self.client.Endpoint.list({
            'endpoint_type': endpoint_type,
            'domain_id': domain_id
        }, metadata=self.transaction.get_connection_meta())
        return self._change_message(response)

    @staticmethod
    def _change_message(message):
        return MessageToDict(message, preserving_proto_field_name=True)
