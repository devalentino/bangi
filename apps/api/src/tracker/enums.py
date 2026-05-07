from enum import Enum


class TrackSource(str, Enum):
    lead = 'lead'
    postback = 'postback'
