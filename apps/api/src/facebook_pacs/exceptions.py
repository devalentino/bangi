from src.core.exceptions import ApplicationError


class BadBusinessPortfolioError(ApplicationError):
    http_status_code = 400
    message = 'Bad Business Manager'


class ExecutorIsAlreadyBindError(ApplicationError):
    http_status_code = 400
    message = 'Executor is already bind'
