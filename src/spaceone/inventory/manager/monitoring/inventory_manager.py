__all__ = ['InventoryManager']

import logging
from spaceone.core.manager import BaseManager
from spaceone.inventory.error import *
from spaceone.inventory.connector.inventory_connector import InventoryConnector

_LOGGER = logging.getLogger(__name__)


class InventoryManager(BaseManager):

    def __init__(self, params):
        self.params = params
        self.inventory_connector: InventoryConnector = self.locator.get_connector('InventoryConnector')

    def get_resources(self, domain_id):

        resource_items = []
        servers = self.inventory_connector.list_servers(self._get_server_query(), domain_id)
        server_list = servers.get('results', [])
        resource_items.extend(server_list)

        # 1차에서는 일단 서버만 해서 돌아가는 것 확인하기
        # cloud_svcs = self.connector.list_cloud_services(self._get_server_query(), domain_id)
        # cloud_svcs_list = cloud_svcs.get('results', [])
        # resource_items.extend(cloud_svcs_list)

        return resource_items

    @staticmethod
    def _get_server_query():
        return {
            "query": {
                "only": [
                    "region_code",
                    "name",
                    "collection_info.secrets",
                    "reference.resource_id",
                    "provider",
                    "data.cloudwatch",
                    "data.stackdriver"
                ]
            }
        }

    @staticmethod
    def _get_cloud_svc_query(provider, flag):
        query = {
            "provider": provider,
            "query": {
                "only": [
                    "name",
                    "region_code",
                    "collection_info.secrets",
                    "reference.resource_id",
                    "provider",
                    "data.cloudwatch",
                    "data.stackdriver"
                ]
            }
        }

        if flag == 'server':
            pass
        else:
            query = {
                "provider": provider,
                "query": {
                    "only": [
                        "name",
                        "region_code",
                        "collection_info.secrets",
                        "reference.resource_id",
                        "provider",
                        "data.cloudwatch",
                        "data.stackdriver"
                    ]
                }
            }
        return query
