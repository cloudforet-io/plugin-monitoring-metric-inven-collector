__all__ = ['InventoryManager']

import logging
from spaceone.core.error import *
from spaceone.core.manager import BaseManager
from spaceone.core.auth.jwt import JWTUtil
from spaceone.core.transaction import Transaction, ERROR_AUTHENTICATE_FAILURE
from spaceone.inventory.connector.inventory_connector import InventoryConnector

_LOGGER = logging.getLogger(__name__)
CLOUD_PROVIDER = ['aws', 'google_cloud', 'azure']


class InventoryManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        #secret_data = kwargs.get('secret_data')
#        endpoint = kwargs.get('endpoint')
#        try:
#            transaction = self._get_transaction(secret_data)
#            self.connector = InventoryConnector(transaction, self._get_config(secret_data, 'inventory'))
#            self.domain_id = secret_data.get('domain_id')
#
#        except Exception as e:
#            print()
#            raise ERROR_UNKNOWN(message=e)

    def init_endpoint(self, endpoint):
        # create client with endpoint
        self.connector = self.locator.get_connector('InventoryConnector', endpoint=endpoint)

    def list_servers(self, provider, domain_id):
        query = self._get_server_query(provider)
        servers = self.connector.list_servers(query, domain_id)
        _LOGGER.debug(f'list_servers: total_count: {servers["total_count"]}')
        return servers

    def list_cloud_services(self, provider, domain_id):
        query = self._get_cloud_svc_query(provider)
        resources = self.connector.list_cloud_services(query, domain_id)
        _LOGGER.debug(f'list_cloud_services: total_count: {resources["total_count"]}')
        return resources

    @staticmethod
    def _get_server_query(provider):
        query = {
            "only": [
                "server_id",
                "provider",
                "region_code",
                "data.compute.account",
                "reference.resource_id",
                "cloud_service_group",
                "cloud_service_type"
            ]
        }
        if provider:
            query.update({
                "filter": [{
                    "k": 'provider',
                    "v": provider,
                    "o": "eq"
                }]
            })
        return query

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
