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

    def __init__(self, **kwargs):
        super().__init__(transaction=None, config=None)
        secret_data = kwargs.get('secret_data')

        try:
            transaction = self._get_transaction(secret_data)
            self.connector = InventoryConnector(transaction, self._get_config(secret_data, 'inventory'))
            self.domain_id = secret_data.get('domain_id')

        except Exception as e:
            print()
            raise ERROR_UNKNOWN(message=e)

    def list_servers(self, provider):
        query = self._get_server_query(provider)
        servers = self.connector.list_servers(query, self.domain_id)
        server_list = servers.get('results', [])
        return server_list

    def list_cloud_services(self):
        cloud_service_resources = []

        for provider in CLOUD_PROVIDER:
            resources = self.connector.list_cloud_services(self._get_cloud_svc_query(provider), self.domain_id)
            cloud_service_resources.extend(resources.get('results', []))

        return cloud_service_resources

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


    @staticmethod
    def _get_server_query(provider):

        query = {
            # 'page': {'limit': 1},
            "only": [
                "server_id",
                "provider",
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
