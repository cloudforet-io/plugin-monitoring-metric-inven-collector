__all__ = ['AWSManager']

import time
import logging
import concurrent.futures
from spaceone.inventory.manager.monitoring.manager import CollectorManager
from pprint import pprint

_LOGGER = logging.getLogger(__name__)
NUM_MAX_INSTANCE = 200
NUM_MAX_INSTANCE = 20


class AWSManager(CollectorManager):
    provider = 'aws'

#    def collect_resources(self, identity_endpoint, domain_id):
#        print("**  AWS monitoring collecting has started **\n")
#
#        start_time = time.time()
#
#        try:
#
#            aws_server_ids = params.get('server_ids').get(self.provider)
#            aws_servers = params.get('servers').get(self.provider)
#            aws_accounts = params.get('accounts').get(self.provider)
#
#            for account in aws_accounts:
#                print(f'@@@ Processing AWS account : {account} @@@ \n')
#                _params = params.copy()
#                _params.update({
#                    'server_ids': aws_server_ids.get(account, []),
#                    'servers': aws_servers.get(account, []),
#                    'account': account,
#                })
#
#                results = self.collect_aws_monitoring_dt_per_accounts(_params)
#                for result in results:
#                    yield result
#
#        except Exception as e:
#            print(f'[ERROR: {e}]')
#            raise e
#
#        print(f' AWS Monitoring data collecting has Finished in  {time.time() - start_time} Seconds')

    def collect_metric_data(self, data_source_id, metric_schema, domain_id) -> list:
        servers = self.inventory_mgr.list_servers(self.provider, domain_id)
        server_group = self._group_server_by_account(servers['results'])
        for account, server_list in server_group.items():
            # get metric_list
            _LOGGER.debug(f'[collect_metric_data] account: {account}, {len(server_list)}')
            # get data
            next_idx = 0
            for idx in range(0, len(server_list), NUM_MAX_INSTANCE):
                if (idx + NUM_MAX_INSTANCE) > len(server_list):
                    next_idx = len(server_list)
                else:
                    next_idx = idx + NUM_MAX_INSTANCE
                # if number of servers is larger than NUM_MAX_INSTANCE, request sub list
                _LOGGER.debug(f'idx: {idx}, next_idx: {next_idx}')
                monitoring_data = self._get_server_metric(server_list[idx: next_idx], data_source_id, metric_schema, domain_id)
                ec2_servers_vos = self.set_metric_data_to_server(metric_schema,
                                                                server_list[idx: next_idx],
                                                                monitoring_data)
                for result in ec2_servers_vos:
                    yield result

    def _group_server_by_account(self, server_list):
        server_group = {}
        for server in server_list:
            account = self._get_account(server)
            if account:
                servers = server_group.get(account, [])
                servers.append(server)
                server_group[account] = servers
        return server_group

    def _get_account(self, server):
        data = server.get('data', {})
        compute = data.get('compute', {})
        account = compute.get('account', None)
        return account

    def _get_server_metric(self, server_list, data_source_id, metric_schema, domain_id):
        server_ids = self._get_server_ids(server_list)
        print(server_ids)
        try:
#            resources_check = self.monitoring_mgr.get_metric_list(data_source_id, 'inventory.Server', server_ids, domain_id)
#            print(resources_check)
#            availble_resources = resources_check.get('availble_resources', [])
#
#            available_resources = self._get_only_available_ids(resources_check.get('available_resources', {}),
#                                                               server_ids)
#
#            # Apply only server that is available for get_metric
            monitoring_data = self.get_servers_metric_data(metric_schema,
                                                           self.provider,
                                                           data_source_id,
                                                           server_ids,
                                                           self.start,
                                                           self.end,
                                                           domain_id)
            return monitoring_data
        except Exception as e:
            print(f'[ERROR: {e}]')
            raise e

    def _get_server_ids(self, server_list):
        server_ids = []
        for server in server_list:
            server_ids.append(server['server_id'])
        return server_ids

#    def collect_aws_monitoring_dt_per_accounts(self, params):
#        _account = params.get('account')
#        server_id_group = self.get_divided_into_max_count(NUM_MAX_INSTANCE, params.get('server_ids'))
#        servers = self.get_divided_into_max_count(NUM_MAX_INSTANCE, params.get('servers'))
#        _total_length = self._get_total_length(server_id_group)
#
#        for idx, server_ids in enumerate(server_id_group, start=0):
#            print(f'No. {idx + 1}\'s : AWS IDs')
#            pprint(server_ids)
#            print()
#
#            print(f"@@@ Processing AWS account:{_account}  {len(server_ids)}/{_total_length} @@@ \n")
#            _params = params.copy()
#            _params.update({'server_ids': server_ids, 'servers': servers[idx]})
#
#            results = self.collect_aws_monitoring_per_ids(_params)
#
#            for result in results:
#                yield result


#    def collect_aws_monitoring_per_ids(self, params):
#        ec2_instance_resources = []
#        # Check available resources
#        server_ids = params.get('server_ids')
#        servers = params.get('servers')
#
#        try:
#            resources_check = self.list_metrics(self.provider, 'inventory.Server', server_ids)
#            available_resources = self._get_only_available_ids(resources_check.get('available_resources', {}),
#                                                               server_ids)
#
#            # Apply only server that is available for get_metric
#            monitoring_data = self.get_servers_metric_data(params.get('metric_schema'),
#                                                           self.provider,
#                                                           available_resources,
#                                                           self.start,
#                                                           self.end) if available_resources else {}
#
#            ec2_servers_vos = self.set_metric_data_to_server(params.get('metric_schema'),
#                                                             servers,
#                                                             monitoring_data)
#
#            ec2_instance_resources.extend(ec2_servers_vos)
#
#        except Exception as e:
#            print(f'[ERROR: {e}]')
#            raise e
#
#        return ec2_instance_resources
