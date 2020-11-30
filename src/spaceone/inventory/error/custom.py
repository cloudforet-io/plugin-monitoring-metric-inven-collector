from spaceone.core.error import ERROR_BASE


class ERROR_REPOSITORY_BACKEND(ERROR_BASE):
    status_code = 'INTERNAL'
    message = 'Repository backend has problem. ({host})'


class ERROR_DRIVER(ERROR_BASE):
    status_code = 'INTERNAL'
    message = '{message}'


class ERROR_NOT_INITIALIZED_EXCEPTION(ERROR_BASE):
    status_code = 'INTERNAL'
    message = 'Collector is not initialized. Please call initialize() method before using it.'


class ERROR_ATHENTICATION_VERIFY(ERROR_BASE):
    message = 'Connection failed. Please check your authentication information.'
