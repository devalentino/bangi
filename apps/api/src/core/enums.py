from enum import Enum


class SortBy(str, Enum):
    id = 'id'
    createdAt = 'createdAt'


class SortOrder(str, Enum):
    asc = 'asc'
    desc = 'desc'


class Currency(str, Enum):
    usd = 'usd'
    eur = 'eur'
    uah = 'uah'


class CostModel(str, Enum):
    cpc = 'cpc'
    cpm = 'cpm'
    cpl = 'cpl'
    cpa = 'cpa'
    cpi = 'cpi'


class LeadStatus(str, Enum):
    accept = 'accept'
    expect = 'expect'
    reject = 'reject'
    trash = 'trash'


class FlowActionType(str, Enum):
    redirect = 'redirect'
    render = 'render'


class FlowSortBy(str, Enum):
    id = 'id'
    createdAt = 'createdAt'
    orderValue = 'orderValue'
