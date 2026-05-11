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
