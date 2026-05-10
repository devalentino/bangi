from src.core.exceptions import ApplicationError, DoesNotExistError


class DomainAlreadyExistsError(ApplicationError):
    http_status_code = 409
    message = 'Domain already exists'


class DomainDoesNotExistError(DoesNotExistError):
    message = 'Domain does not exist'


class CampaignAlreadyBoundError(ApplicationError):
    http_status_code = 400
    message = 'Campaign is already attached to a domain'


class DashboardDomainCannotAttachCampaignError(ApplicationError):
    http_status_code = 400
    message = 'Dashboard domains cannot be attached to campaigns'
