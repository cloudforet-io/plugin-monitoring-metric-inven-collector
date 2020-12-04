import logging

from google.protobuf.json_format import MessageToDict

from spaceone.core.connector import BaseConnector
from spaceone.core import pygrpc
from spaceone.core.utils import parse_endpoint
from spaceone.core.error import *

__all__ = ['MonitoringConnector']

_LOGGER = logging.getLogger(__name__)


class MonitoringConnector(BaseConnector):

    def __init__(self, transaction, config):
        super().__init__(transaction, config)
        self._check_config()
        self._init_client()

    def _init_client(self):
        for version, uri in self.config['endpoint'].items():
            e = parse_endpoint(uri)
            self.client = pygrpc.client(endpoint=f'{e.get("hostname")}:{e.get("port")}', version=version)

    def _check_config(self):
        if 'endpoint' not in self.config:
            raise ERROR_CONNECTOR_CONFIGURATION(backend=self.__class__.__name__)

        if len(self.config['endpoint']) > 1:
            raise ERROR_CONNECTOR_CONFIGURATION(backend=self.__class__.__name__)

    def list_data_source(self, query, domain_id):
        response = self.client.DataSource.list({
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