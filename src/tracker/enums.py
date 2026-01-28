from enum import Enum


class Status(str, Enum):
    approved = 'approved'
    rejected = 'rejected'
    trash = 'trash'
