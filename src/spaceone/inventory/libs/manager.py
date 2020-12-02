from spaceone.core.manager import BaseManager
from spaceone.inventory.libs.connector import GoogleCloudConnector


class GoogleCloudManager(BaseManager):
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
        regions, zones = self.list_regions_zones(params['secret_data'])
        params.update({
            'regions': regions,
            'zones': zones
        })

        return self.collect_power_state(params)

    def list_regions_zones(self, secret_data):
        result_regions = []
        result_zones = []

        query = {}

        if secret_data.get('region_name'):
            region_self_link = f'https://www.googleapis.com/compute/v1/projects/{secret_data["project_id"]}/regions/{secret_data.get("region_name")}'
            query.update({'filter': f'region="{region_self_link}"'})

        connector: GoogleCloudConnector = self.locator.get_connector('GoogleCloudConnector', secret_data=secret_data)
        zones = connector.list_zones(**query)

        for zone in zones:
            result_zones.append(zone.get('name'))

            if region := zone.get('region'):
                result_regions.append(region.split('/')[-1])

        return list(set(result_regions)), result_zones
