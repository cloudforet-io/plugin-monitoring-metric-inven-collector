import time
import logging
import concurrent.futures
from spaceone.core.service import *
from spaceone.inventory.libs.manager import GoogleCloudManager
from spaceone.inventory.manager.collector_manager import CollectorManager

_LOGGER = logging.getLogger(__name__)
MAX_WORKER = 20
SUPPORTED_RESOURCE_TYPE = ['inventory.Server', 'inventory.CloudService']
FILTER_FORMAT = []


@authentication_handler
class CollectorService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)

        self.collector_manager: CollectorManager = self.locator.get_manager('CollectorManager')

    @check_required(['options'])
    def init(self, params):
        """ init plugin by options
        """
        capability = {
            'filter_format': FILTER_FORMAT,
            'supported_resource_type': SUPPORTED_RESOURCE_TYPE
        }
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
        options = params['options']
        secret_data = params.get('secret_data', {})
        if secret_data != {}:
            google_manager = GoogleCloudManager()
            active = google_manager.verify({}, secret_data)

        return {}

    @transaction
    @check_required(['options', 'secret_data', 'filter'])
    def list_resources(self, params):
        # thread 필요?
        """ Get quick list of resources
        Args:
            params:
                - options
                - secret_data
                - filter

        Returns: list of resources
        """

        start_time = time.time()
        for resource in self.collector_manager.list_resources(params):
            yield resource.to_primitive()

        print(f'############## TOTAL FINISHED {time.time() - start_time} Sec ##################')

    # @transaction
    # @check_required(['options', 'secret_data', 'filter'])
    # def list_resources(self, params):
    #     """
    #     Args:
    #         params:
    #             - options
    #             - schema
    #             - secret_data
    #             - filter
    #     """
    #
    #     start_time = time.time()
    #
    #     # TODO: Thread per cloud services
    #     with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
    #         print("[ EXECUTOR START ]")
    #         future_executors = []
    #         for execute_manager in self.execute_managers:
    #             print(f'@@@ {execute_manager} @@@')
    #             _manager = self.locator.get_manager(execute_manager)
    #             future_executors.append(executor.submit(_manager.collect_resources, params))
    #
    #         for future in concurrent.futures.as_completed(future_executors):
    #             for resource in future.result():
    #                 yield resource.to_primitive()
    #
    #     print(f'############## TOTAL FINISHED {time.time() - start_time} Sec ##################')


