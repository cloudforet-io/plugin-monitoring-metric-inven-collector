from spaceone.core.manager import BaseManager
from spaceone.inventory.libs.connector import GoogleCloudConnector


class CollectManager(BaseManager):
    connector_name = None
    cloud_service_types = []
    response_schema = None
    collected_region_codes = []

    def verify(self, options, secret_data, **kwargs):
        """ Check collector's status.
        """
        connector: GoogleCloudConnector = self.locator.get_connector('GoogleCloudConnector', secret_data=secret_data)
        connector.verify()

    def collect_power_state(self, params) -> list:
        raise NotImplemented

    def collect_resources(self, params) -> list:
        # Add zone lists in params

        return self.collect_power_state(params)
