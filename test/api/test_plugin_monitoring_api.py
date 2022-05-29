import os
import unittest
import json

from spaceone.core.unittest.runner import RichTestRunner
from spaceone.tester import TestCase, print_json
from pprint import pprint


api_key = os.environ.get('API_KEY')
api_key_id = os.environ.get('API_KEY_ID')
endpoint = os.environ.get('ENDPOINT')

SECRET = {
    'api_key': api_key,
    'api_key_id': api_key_id,
    'endpoint': endpoint
}

class TestCollector(TestCase):

    def test_init(self):
        v_info = self.inventory.Collector.init({'options': {}})
        print_json(v_info)

    def _test_verify(self):
        options = {}
        v_info = self.inventory.Collector.verify({'options': options, 'secret_data': SECRET})
        print_json(v_info)

    def test_collect(self):
        options = {'endpoint_type': 'public',
                   'supported_metrics': [
                       {'provider': 'aws', 'resource_type': 'inventory.Server',
                        'metric': ['disk.write_throughput']}
                   ],
                   'supported_period': 14
                   }
        options = {'endpoint_type': 'public',
                   'supported_period': 14
                   }
 
        filter = {}

        resource_stream = self.inventory.Collector.collect({'options': options, 'secret_data': SECRET,
                                                            'filter': filter})
        # print(resource_stream)

        for res in resource_stream:
            print_json(res)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
