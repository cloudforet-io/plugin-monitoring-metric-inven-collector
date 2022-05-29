import time
import logging
import traceback
from spaceone.core.transaction import Transaction
from spaceone.core.service import authentication_handler
from spaceone.core.service import check_required
from spaceone.core.service import transaction
from spaceone.core.service import BaseService
from spaceone.core.auth.jwt import JWTUtil
from spaceone.core.transaction import ERROR_AUTHENTICATE_FAILURE
from spaceone.inventory.manager.collector.aws_manager import AWSManager

_LOGGER = logging.getLogger(__name__)

SUPPORTED_RESOURCE_TYPE = ['inventory.Server', 'inventory.CloudService']
# flag that checks if get_connection based on region
PROVIDER_REGION_FILTER = {
    'aws': True,
    'google_cloud': False,
    'azure': False,
}
FILTER_FORMAT = []


@authentication_handler
class CollectorService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.execute_managers = [
#            'AzureManager',
#            'GoogleCloudManager',
            'AWSManager',
        ]

    @check_required(['options'])
    def init(self, params):
        """ init plugin by options
        """
        capability = {
            'filter_format': FILTER_FORMAT,
            'supported_resource_type': SUPPORTED_RESOURCE_TYPE
        }
        supported_metrics = []
        default_metrics = []

        for execute_manager in self.execute_managers:
            mon_mgr = self.locator.get_manager(execute_manager)
            supported_metrics.extend(mon_mgr.list_supported_metrics())
            default_metrics.extend(mon_mgr.list_default_metrics())

        capability['supported_metrics'] = supported_metrics
        capability['default_metrics'] = default_metrics

        return {'metadata': capability}

    @transaction
    @check_required(['options', 'secret_data'])
    def verify(self, params):
        """
        Args:
              params:
                - options
                - secret_data
        """
        #options = params['options']
        self._check_secret_data(params['secret_data'])
        return {}

    @transaction
    @check_required(['options', 'secret_data', 'filter'])
    def list_resources(self, params):
        """
        Args:
            params:
                - options
                - schema
                - secret_data
                - filter
        """
        start_time = time.time()
        print("[ EXECUTOR START: Monitoring Metric Collector ]")

        secret_data = params['secret_data']
        options = params['options']
        self._check_secret_data(secret_data)

        api_key = secret_data['api_key']
        domain_id = self._extract_domain_id(api_key)
        identity_endpoint = secret_data['endpoint']
        endpoint_type = options.get('endpoint_type', 'internal')
        # endpoint_type = internal(default) | public
        supported_metrics = options.get('supported_metrics', {})
        supported_period = options.get('supported_period', 1)
        """
        'supported_metrics': [
           {'provider': 'aws', 'resource_type': 'inventory.Server',
           'metric': ['cpu.utilization', 'disk.write_throughput']}
        ]
        """
        # Add token at transaction,
        # since this plugin will call other micro services(identity, inventory, monitoring)
        self.transaction.set_meta('token', api_key)

        for execute_manager in self.execute_managers:
            print(f'@@@ {execute_manager} @@@ \n')
            mon_mgr = self.locator.get_manager(execute_manager)

            results = mon_mgr.collect_resources(identity_endpoint, endpoint_type, domain_id,
                                                supported_metrics, supported_period)
            for result in results:
                yield result.to_primitive()

        print(f'TOTAL TIME : {time.time() - start_time} Seconds')

    @staticmethod
    def _extract_domain_id(token):
        try:
            decoded = JWTUtil.unverified_decode(token)
            return decoded.get('did')
        except Exception:
            _LOGGER.debug(f'[ERROR_AUTHENTICATE_FAILURE] token: {token}')
            raise ERROR_AUTHENTICATE_FAILURE(message='Cannot decode token.')

    @staticmethod
    def _check_secret_data(secret_data):
        """
        api_key_id(str)
        api_key(str)
        endpoint(str)
        """
        pass
