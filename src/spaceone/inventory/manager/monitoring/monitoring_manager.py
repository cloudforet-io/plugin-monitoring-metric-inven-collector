__all__ = ['MonitoringManager']

import logging
from spaceone.core.error import *
from spaceone.core.manager import BaseManager
from spaceone.core.auth.jwt import JWTUtil
from spaceone.core.transaction import Transaction, ERROR_AUTHENTICATE_FAILURE
from spaceone.inventory.connector.monitoring_connector import MonitoringConnector
from pprint import pprint

_LOGGER = logging.getLogger(__name__)


class MonitoringManager(BaseManager):

    def __init__(self, **kwargs):
        super().__init__(transaction=None, config=None)
        secret_data = kwargs.get('secret_data')

        try:
            transaction = self._get_transaction(secret_data)
            self.connector = MonitoringConnector(transaction, self._get_config(secret_data, 'monitoring'))
            self.domain_id = secret_data.get('domain_id')

        except Exception as e:
            print()
            raise ERROR_UNKNOWN(message=e)

    def list_data_source(self):
        query = self._get_data_source_query()
        data_sources = self.connector.list_data_source(query, self.domain_id)
        data_source_list = data_sources.get('results', [])
        return data_source_list

    def get_metric_list(self, data_source_id, resource_type, resources):
        param = {
            'data_source_id': data_source_id,
            'resource_type': resource_type,
            'resources': [resources]
        }
        metrics = self.connector.metric_list(param, self.domain_id)
        metric_list = metrics.get('metrics', [])
        return metric_list

    def get_metric_data(self, data_source_id, resource_type, resource, metric, start, end, period, stat):

        metrics = {'domain_id': self.domain_id,
                   'labels': [],
                   'resource_values': {}
                   }

        metric_resources = [resource] if isinstance(resource, str) else resource

        param = {
            'data_source_id': data_source_id,
            'resource_type': resource_type,
            'resources': metric_resources,
            'metric': metric,
            'start': start,
            'end': end,
        }
        if period:
            param.update({'period': period})

        if stat:
            param.update({'stat': stat})

        try:
            metrics = self.connector.metric_get_data(param, self.domain_id)
        except Exception as e:
            print(f'[ERROR: {e}]')

        return metrics

    @staticmethod
    def _get_data_source_query():
        query = {}
        # Please, update filter option for further use if it needs
        query.update({
            "filter": [{
                "k": 'monitoring_type',
                "v": 'METRIC',
                "o": "eq"
            }]
        })

        return query

    @staticmethod
    def _get_transaction(secret_data):
        return Transaction({'token': secret_data.get('api_key', None)})

    @staticmethod
    def _get_config(secret_data, service_name):
        end_point_list = secret_data.get('end_point_list', [])
        for end_point in end_point_list:
            if end_point.get('service') == service_name:
                ep = end_point.get('endpoint')
                return {
                    "endpoint": {
                        ep[ep.rfind('/') + 1:]: ep[0:ep.rfind('/')]
                    }
                }
