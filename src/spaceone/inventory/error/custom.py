from spaceone.core.error import ERROR_BASE
from spaceone.core.error import ERROR_INVALID_ARGUMENT


class ERROR_REPOSITORY_BACKEND(ERROR_BASE):
    status_code = 'INTERNAL'
    message = 'Repository backend has problem. ({host})'


class ERROR_DRIVER(ERROR_BASE):
    status_code = 'INTERNAL'
    message = '{message}'


class ERROR_NOT_FOUND_API_KEY(ERROR_BASE):
    message = 'Not found api_key. (api_key = {api_key})'


class ERROR_API_KEY(ERROR_BASE):
    message = 'api_key is not appropriate to get connector. (api_key = {api_key})'


class ERROR_NOT_INITIALIZED_EXCEPTION(ERROR_BASE):
    status_code = 'INTERNAL'
    message = 'Collector is not initialized. Please call initialize() method before using it.'


class ERROR_ATHENTICATION_VERIFY(ERROR_BASE):
    message = 'Connection failed. Please check your authentication information.'


class ERROR_NOT_SUPPORT_STAT(ERROR_INVALID_ARGUMENT):
    _message = 'collector stat is invalid. (supported_stat = {supported_stat})'


class ERROR_NOT_SUPPORT_METRIC_FORMAT(ERROR_INVALID_ARGUMENT):
    _message = 'metric format is invalid. (metric_format = {metric_format})'


class ERROR_ENDPOINT_NOT_FOUND(ERROR_BASE):
    _message = 'endpoint:{service} is not found'
