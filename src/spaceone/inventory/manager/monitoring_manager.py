__all__ = ['MonitoringManager']

import logging
from spaceone.core import utils
from spaceone.core.error import *
from spaceone.core.manager import BaseManager
from datetime import datetime
from spaceone.core.transaction import Transaction, ERROR_AUTHENTICATE_FAILURE
from spaceone.inventory.connector.monitoring_connector import MonitoringConnector
from pprint import pprint


_LOGGER = logging.getLogger(__name__)


class MonitoringManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_endpoint(self, endpoint):
        # create client with endpoint
        self.connector = self.locator.get_connector('MonitoringConnector', endpoint=endpoint)

    def get_data_source(self, provider, domain_id):
        query = self._get_data_source_query()
        data_sources = self.connector.list_data_source(provider, query, domain_id)
        data_source_list = data_sources.get('results', [])
        return data_source_list

    def get_metric_data(self, data_source_id, resource_type, resources, metric, start, end, domain_id, period, stat):

        param = {
            'data_source_id': data_source_id,
            'resource_type': resource_type,
            'resources': resources,
            'metric': metric,
            'stat': stat,
            'start': utils.datetime_to_iso8601(start),
            'end': utils.datetime_to_iso8601(end),
        }

        # TODO: choonho, This is AWS specific
        param.update({'period': period * 86400})

        try:
            metrics = self.connector.metric_get_data(param, domain_id)
        except Exception as e:
            print('##################################')
            print(f'[ERROR: {e}]')
            print('##################################')
            metrics = {'domain_id': domain_id,
                       'labels': [],
                       'resource_values': {}
                       }

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
