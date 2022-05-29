__all__ = ['IdentityManager']

import logging
from spaceone.core.error import *
from spaceone.core.manager import BaseManager
from spaceone.core.auth.jwt import JWTUtil
from spaceone.core.transaction import Transaction, ERROR_AUTHENTICATE_FAILURE
from spaceone.inventory.connector.identity_connector import IdentityConnector

from spaceone.inventory.error.custom import ERROR_ENDPOINT_NOT_FOUND

_LOGGER = logging.getLogger(__name__)


class IdentityManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_endpoints(self, identity_endpoint, endpoint_type, domain_id):
        """
        get endpoints of services
        """
        self.connector = self.locator.get_connector('IdentityConnector', endpoint=identity_endpoint)
        endpoints = self.connector.get_end_points(domain_id, endpoint_type)
        return endpoints['results']
