__all__ = ['InventoryManager']

import logging
from spaceone.core.manager import BaseManager
from spaceone.inventory.error import *
from spaceone.core.transaction import Transaction
from spaceone.inventory.connector.inventory_connector import InventoryConnector

_LOGGER = logging.getLogger(__name__)
CLOUD_PROVIDER = ['aws', 'google_cloud', 'azure']


class InventoryManager(BaseManager):

    def __init__(self, params, **kwargs):
        self.params = params
        self.domain_id = None
        self.connector = None
        super().__init__(**kwargs)

    def set_connector(self):
        transaction, inventory_config, domain_id = self._get_connect_config(self.params.get('secret_data', {}))
        self.connector = InventoryConnector(transaction, inventory_config)
        self.domain_id = domain_id

    def list_servers(self):
        query = self._get_server_query()
        servers = self.connector.list_servers(query, self.domain_id)
        server_list = servers.get('results', [])
        return server_list

    providers = {'aws': [],
                 'google_cloud': [],
                 'azure': []
                 }

    def list_cloud_services(self):
        cloud_service_resources = []

        for provider in CLOUD_PROVIDER:
            resources = self.connector.list_cloud_services(self._get_cloud_svc_query(provider), self.domain_id)
            cloud_service_resources.extend(resources.get('results', []))

        return cloud_service_resources

    @staticmethod
    def _get_connect_config(config_data):
        transaction = Transaction({
            'token': config_data.get('access_token', None)
        })
        inventory_config = config_data.get('InventoryConnector', None)
        return transaction, inventory_config, config_data.get('domain_id')

    @staticmethod
    def _get_server_query():
        return {
            "only": [
                "server_id",
                "region_code",
                "name",
                "collection_info.secrets",
                "reference.resource_id",
                "provider",
                "data.cloudwatch",
                "data.stackdriver"
            ]
        }

    @staticmethod
    def _get_cloud_svc_query(provider):
        cloud_service_filters = {
            'aws': {
                'cloud_service_group': ["EC2", "S3", "RDS", "DocumentDB"],
                'cloud_service_type': ["Volume", "Bucket", "Database", "Cluster"]
            },
            'google_cloud': {
                'cloud_service_group': ['ComputeEngine', 'CloudSQL'],
                'cloud_service_type': ['Disk', 'Instance']
            },
            'azure': {
                'cloud_service_group': [],
                'cloud_service_type': []
            }
        }

        filter_contents = cloud_service_filters.get(provider)

        return {
            "filter": [{
                "k": 'provider',
                "v": provider,
                "o": "eq"
                },
                {
                    "k": 'cloud_service_group',
                    "v": filter_contents.get('cloud_service_group'),
                    "o": "in"
                },
                {
                    "k": 'cloud_service_type',
                    "v": filter_contents.get('cloud_service_type'),
                    "o": "in"
                }
            ],
            "only": ["cloud_service_id",
                     "cloud_service_group",
                     "cloud_service_type",
                     "reference.resource_id",
                     "data.cloudwatch",
                     "data.stackdriver",
                     "provider"

                     ]
        }
