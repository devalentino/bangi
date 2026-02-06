from enum import Enum


class ExpenseSortBy(str, Enum):
    id = 'id'
    createdAt = 'createdAt'
    date = 'date'
