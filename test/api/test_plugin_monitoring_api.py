import os
import unittest
import json

from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core.transaction import Transaction
from spaceone.tester import TestCase, print_json
from spaceone.core import utils

config_path = os.environ.get('TEST_CONFIG', None)

if config_path is None:
    print("""
        ##################################################
        # ERROR 
        #
        # Configure your credential first for test
        # https://console.cloud.google.com/apis/credentials

        ##################################################
        example)

        export TEST_CONFIG="<PATH>" 
    """)
    exit


def _get_configs():
    return utils.load_yaml_from_file(config_path)

class TestCollectors(TestCase):

    # def test_init(self):
    #     v_info = self.inventory.Collector.init({'options': {}})
    #     print_json(v_info)
    #
    # def test_verify(self):
    #     options = {}
    #     secret_data = _get_credentials()
    #     v_info = self.inventory.Collector.verify({'options': options, 'secret_data': secret_data})
    #     print_json(v_info)

    def test_collect(self):
        config = _get_configs()
        self.domain_id = config.get('domain_id')
        self.connector_conf = config.get('InventoryConnector')
        self.transaction = Transaction({
            'token': config.get('access_token')
        })

        options = {}

        resource_stream = self.inventory.Collector.collect({'options': options})
        # print(resource_stream)

        for res in resource_stream:
            print_json(res)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
