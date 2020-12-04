__all__ = ['IdentityManager']

import logging
from spaceone.core.manager import BaseManager
from spaceone.core.auth.jwt import JWTAuthenticator, JWTUtil
from spaceone.core.transaction import Transaction, ERROR_AUTHENTICATE_FAILURE
from spaceone.inventory.connector.identity_connector import IdentityConnector
from pprint import pprint
_LOGGER = logging.getLogger(__name__)
CLOUD_PROVIDER = ['aws', 'google_cloud', 'azure']


class IdentityManager(BaseManager):

    def __init__(self, params, **kwargs):
        self.params = params
        self.connector = None
        self.domain_id = None
        super().__init__(**kwargs)

    def set_connector(self):
        secret_data = self.params.get('secret_data')
        print('secret_data')
        print()
        pprint(secret_data)

        try:
            ep = secret_data.get('endpoint')
            transaction = Transaction({'token': secret_data.get('api_key', None)})
            identity_config = {
                "endpoint": {
                    ep[ep.rfind('/') + 1:]: ep[0:ep.rfind('/')]
                }
            }

            domain_id = self._extract_domain_id(secret_data.get('api_key', None))
            print('apiKey')
            print(secret_data.get('api_key', None))
            print()
            print(f'identity_endpoint: {identity_config}')
            print()
            print(f'domain_id: {domain_id}')
            self.connector = IdentityConnector(transaction, identity_config)
            self.domain_id = domain_id

        except Exception as e:
            print(f'[ERROR: {e}]')

    def list_endpoints(self):
        end_points = self.connector.get_end_points()
        results = end_points.get('results', [])
        return results

    @staticmethod
    def _extract_domain_id(token):
        try:
            decoded = JWTUtil.unverified_decode(token)
        except Exception:
            _LOGGER.debug(f'[ERROR_AUTHENTICATE_FAILURE] token: {token}')
            raise ERROR_AUTHENTICATE_FAILURE(message='Cannot decode token.')

        domain_id = decoded.get('did')

        if domain_id is None:
            raise ERROR_AUTHENTICATE_FAILURE(message='Empty domain_id provided.')

        return domain_id

