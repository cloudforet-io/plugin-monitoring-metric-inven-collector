__all__ = ['CollectorManager']

import time
import logging
from spaceone.core.manager import BaseManager
from spaceone.inventory.connector.inventory_connector import InventoryConnector
from spaceone.inventory.connector.monitoring_connector import MonitoringConnector
from spaceone.inventory.manager.monitoring.inventory_manager import InventoryManager
from spaceone.inventory.manager.monitoring.monitoring_plugin_manager import MonitoringPluginManager

_LOGGER = logging.getLogger(__name__)


class CollectorManager(BaseManager):

    def __init__(self, transaction):
        self.secret = None  # secret info for update meta
        super().__init__(transaction)

    def verify(self, secret_data, region_name):
        """
            Check connection
        """
        return ''

    def list_resources(self, params):
        inventory_manager: InventoryManager = InventoryManager(params)
        monitoring_manager: MonitoringPluginManager = MonitoringPluginManager(params)

        domain_id = params.get('domain_id')

        try:
            #get servers

            #get cloud services

            collecting_items = inventory_manager.get_resources(domain_id)
            return collecting_items

        except Exception as e:
            print(f'[ERROR: {params["region_name"]}] : {e}')
            raise e

