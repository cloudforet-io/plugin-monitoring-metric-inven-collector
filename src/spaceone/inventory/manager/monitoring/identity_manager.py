__all__ = ['IdentityManager']

import logging
from spaceone.core.error import *
from spaceone.core.manager import BaseManager
from spaceone.core.auth.jwt import JWTUtil
from spaceone.core.transaction import Transaction, ERROR_AUTHENTICATE_FAILURE
from spaceone.inventory.connector.identity_connector import IdentityConnector
_LOGGER = logging.getLogger(__name__)


class IdentityManager(BaseManager):

    def __init__(self, **kwargs):
        super().__init__(transaction=None, config=None)
        secret_data = kwargs.get('secret_data')

        try:
            transaction = self._get_transaction(secret_data)
            identity_config = self._get_config(secret_data)
            self.connector = IdentityConnector(transaction, identity_config)
            self.domain_id = self._extract_domain_id(secret_data.get('api_key', None))

        except Exception as e:
            print()
            raise ERROR_UNKNOWN(message=e)

    def list_endpoints(self):
        end_points = self.connector.get_end_points(self.domain_id)
        results = end_points.get('results', [])
        return results

    @staticmethod
    def _get_transaction(secret_data):
        return Transaction({'token': secret_data.get('api_key', None)})

    @staticmethod
    def _get_config(secret_data):
        ep = secret_data.get('endpoint')
        return {
            "endpoint": {
                ep[ep.rfind('/') + 1:]: ep[0:ep.rfind('/')]
            }
        }

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

