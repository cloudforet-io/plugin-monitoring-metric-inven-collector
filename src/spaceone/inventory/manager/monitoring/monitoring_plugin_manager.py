__all__ = ['MonitoringPluginManager']

import logging
from spaceone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)


class MonitoringPluginManager(BaseManager):
    def __init__(self, params, monitoring_plugin_connector=None):
        self.params = params
        self.connector = monitoring_plugin_connector

    def get_metric_data(self, schema, options, secret_data, resource, metric, start, end, period, stat):
        return self.connector.get_metric_data(schema, options, secret_data, resource, metric, start, end, period, stat)

