from enum import Enum


class DomainPurpose(str, Enum):
    campaign = 'campaign'
    dashboard = 'dashboard'


class DomainCookieName(str, Enum):
    flow_id = 'flow_id'


class DomainSortBy(str, Enum):
    id = 'id'
    createdAt = 'createdAt'
    hostname = 'hostname'
    purpose = 'purpose'
    campaignId = 'campaignId'
    isARecordSet = 'isARecordSet'
    isDisabled = 'isDisabled'


class DomainCertificateStatus(str, Enum):
    pending = 'pending'
    active = 'active'
    failed = 'failed'
    expired = 'expired'


class DomainCertificateCa(str, Enum):
    letsencrypt = 'letsencrypt'


class DomainCertificateValidationMethod(str, Enum):
    http_01_webroot = 'http-01-webroot'
