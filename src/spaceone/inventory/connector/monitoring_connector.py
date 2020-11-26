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
        self.client = None

    def initialize(self, endpoint):
        e = parse_endpoint(endpoint)
        self.client = pygrpc.client(endpoint=f'{e.get("hostname")}:{e.get("port")}', version='plugin')

    def init(self, options):
        response = self.client.DataSource.init({
            'options': options,
        }, metadata=self.transaction.get_connection_meta())

        return self._change_message(response)
        # return response

    def verify(self, schema, options, secret_data):
        params = {
            'options': options,
            'secret_data': secret_data
        }

        if schema:
            params.update({
                'schema': schema
            })

        self.client.DataSource.verify(params, metadata=self.transaction.get_connection_meta())

    def list_metrics(self, schema, options, secret_data, resource):
        params = {
            'options': options,
            'secret_data': secret_data,
            'resource': resource
        }

        if schema:
            params.update({
                'schema': schema
            })

        responses = self.client.Metric.list(params, metadata=self.transaction.get_connection_meta())
        message = self._change_message(responses)
        return message

    def get_metric_data(self, schema, options, secret_data, resource, metric, start, end, period, stat):
        params = {
            'options': options,
            'secret_data': secret_data,
            'resource': resource,
            'metric': metric,
            'start': start,
            'end': end,
            'period': period,
            'stat': stat
        }

        if schema:
            params.update({
                'schema': schema
            })

        responses = self.client.Metric.get_data(params, metadata=self.transaction.get_connection_meta())
        return self._change_message(responses)

    def list_logs(self, schema, options, secret_data, resource, plugin_filter, start, end, sort, limit):
        params = {
            'options': options,
            'secret_data': secret_data,
            'resource': resource,
            'filter': plugin_filter,
            'start': start,
            'end': end,
            'sort': sort,
            'limit': limit
        }

        if schema:
            params.update({
                'schema': schema
            })

        responses = self.client.Log.list(params, metadata=self.transaction.get_connection_meta())

        for response in responses:
            yield self._change_message(response)

    @staticmethod
    def _change_message(message):
        return MessageToDict(message, preserving_proto_field_name=True)