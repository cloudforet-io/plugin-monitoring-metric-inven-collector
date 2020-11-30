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

    def get_metric_data(self, schema, options, secret_data, resource, metric, start, end, period, stat):

        return self.connector.get_metric_data(schema, options, secret_data, resource, metric, start, end, period, stat)

    @staticmethod
    def _get_connect_config(config_data):
        transaction = Transaction({
            'token': config_data.get('access_token', None)
        })
        inventory_config = config_data.get('MonitoringPluginConnector', None)
        return transaction, inventory_config, config_data.get('domain_id')