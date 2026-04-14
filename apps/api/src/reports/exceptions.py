from src.core.exceptions import ApplicationError


class ExpensesDistributionParameterError(ApplicationError):
    http_status_code = 400
    message = 'Bad distribution parameter'


class ClickDoesNotExistError(ApplicationError):
    http_status_code = 404
    message = 'Click does not exist'
