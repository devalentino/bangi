class ApplicationError(Exception):
    http_status_code = 500
    message = 'Application failed'
