from enum import Enum


class SortBy(str, Enum):
    id = 'id'
    created_at = 'created_at'


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


class FlowActionType(str, Enum):
    redirect = 'redirect'
    render = 'render'
