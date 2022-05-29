import logging

from google.protobuf.json_format import MessageToDict

from spaceone.core.connector import BaseConnector
from spaceone.core import pygrpc
from spaceone.core.utils import parse_grpc_endpoint
from spaceone.core.error import *
from pprint import pprint
__all__ = ['MonitoringConnector']

_LOGGER = logging.getLogger(__name__)


class MonitoringConnector(BaseConnector):

    def __init__(self, transaction, config, **kwargs):
        super().__init__(transaction, config, **kwargs)
        e = parse_grpc_endpoint(self.endpoint)
        _LOGGER.debug(f'endpoint: {e}')
        self.client = pygrpc.client(endpoint=e['endpoint'], ssl_enabled=e['ssl_enabled'])

    def list_data_source(self, provider, query, domain_id):
        response = self.client.DataSource.list({
            'provider': provider,
            'query': query,
            'domain_id': domain_id
        }, metadata=self.transaction.get_connection_meta())

        return self._change_message(response)

    def metric_list(self, param, domain_id):
        param.update({'domain_id': domain_id})

        response = self.client.Metric.list(param, metadata=self.transaction.get_connection_meta())
        return self._change_message(response)

    def metric_get_data(self, param, domain_id):
        param.update({'domain_id': domain_id})

        try:
            response = self.client.Metric.get_data(param, metadata=self.transaction.get_connection_meta())
            return self._change_message(response)

        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

    @staticmethod
    def _change_message(message):
        return MessageToDict(message, preserving_proto_field_name=True)
