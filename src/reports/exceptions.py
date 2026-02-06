from src.core.exceptions import ApplicationError


class ExpensesDistributionParameterError(ApplicationError):
    http_status_code = 400
    message = 'Bad distribution parameter'
