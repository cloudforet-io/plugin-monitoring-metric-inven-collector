__all__ = ['MonitoringManager']

import logging
from spaceone.core.manager import BaseManager
from spaceone.inventory.error import *
from spaceone.core.transaction import Transaction
from spaceone.inventory.connector.monitoring_connector import MonitoringConnector

_LOGGER = logging.getLogger(__name__)


class MonitoringManager(BaseManager):

    def __init__(self, params, **kwargs):
        self.params = params
        self.domain_id = None
        self.connector = None
        super().__init__(**kwargs)

    def set_connector(self):
        transaction, inventory_config, domain_id = self._get_connect_config(self.params.get('secret_data', {}))
        self.connector = MonitoringConnector(transaction, inventory_config)
        self.domain_id = domain_id

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
        metric_resources = []
        if isinstance(resource, str):
            metric_resources.append(resource)
        else:
            metric_resources = resource

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

        metrics = self.connector.metric_get_data(param, self.domain_id)
        return metrics

    @staticmethod
    def _get_connect_config(config_data):
        transaction = Transaction({
            'token': config_data.get('access_token')
        })
        inventory_config = config_data.get('MonitoringConnector')
        return transaction, inventory_config, config_data.get('domain_id')

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
