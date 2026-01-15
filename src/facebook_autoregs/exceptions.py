from src.core.exceptions import ApplicationError


class ExecutorDoesNotExist(ApplicationError):
    http_status_code = 404
    message = 'Executor does not exist'


class BadBusinessPortfolioError(ApplicationError):
    http_status_code = 400
    message = 'Bad Business Manager'
