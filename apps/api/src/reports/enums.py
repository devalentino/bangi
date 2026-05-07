from enum import Enum


class ExpenseSortBy(str, Enum):
    id = 'id'
    createdAt = 'createdAt'
    date = 'date'


class DiscardWindow(str, Enum):
    m5 = '5m'
    h1 = '1h'
    d1 = '1d'


class DiscardGroupBy(str, Enum):
    country = 'country'
    browserFamily = 'browserFamily'
    osFamily = 'osFamily'
    isMobile = 'isMobile'
    deviceFamily = 'deviceFamily'
    isBot = 'isBot'
