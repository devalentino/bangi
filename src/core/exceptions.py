class ApplicationError(Exception):
    http_status_code = 500
    message = 'Application failed'


class LandingPageUploadError(ApplicationError):
    http_status_code = 400
    message = 'Can\'t store landing page'


class DoesNotExistError(ApplicationError):
    http_status_code = 404
    message = 'Does not exist'
