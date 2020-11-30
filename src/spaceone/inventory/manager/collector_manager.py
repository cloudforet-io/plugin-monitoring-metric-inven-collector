__all__ = ['CollectorManager']

import time
import logging
from spaceone.core.manager import BaseManager
from spaceone.inventory.connector.inventory_connector import InventoryConnector
from spaceone.inventory.connector.monitoring_connector import MonitoringConnector
from spaceone.inventory.manager.monitoring.inventory_manager import InventoryManager
from spaceone.inventory.manager.monitoring.monitoring_manager import MonitoringManager
from spaceone.core.transaction import Transaction
from pprint import pprint
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
        resources = []

        inventory_manager: InventoryManager = InventoryManager(params)
        inventory_manager.set_connector()

        monitoring_manager: MonitoringManager = MonitoringManager(params)
        monitoring_manager.set_connector()

        try:
            servers = inventory_manager.list_servers()
            resources.extend(servers)

            cloud_services = inventory_manager.list_cloud_services()
            resources.extend(cloud_services)





        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

        return []

