import types
from dataclasses import dataclass, field, fields
from random import randint
from typing import Union, get_args, get_origin

from rule_engine import Context, ast


@dataclass
class Client:
    browser_family: str | None
    device_family: str | None
    os_family: str | None
    country: str | None
    is_bot: bool
    is_mobile: bool
    roll: int = field(default_factory=lambda: randint(1, 100))

    @staticmethod
    def _rule_data_type(annotation):
        origin = get_origin(annotation)
        if origin in (types.UnionType, Union):
            args = [arg for arg in get_args(annotation) if arg is not type(None)]
            if len(args) == 1:
                annotation = args[0]
            else:
                return ast.DataType.UNDEFINED
        try:
            return ast.DataType.from_type(annotation)
        except (TypeError, ValueError):
            return ast.DataType.UNDEFINED

    @classmethod
    def rule_engine_context(cls):
        type_map = {field.name: cls._rule_data_type(field.type) for field in fields(Client)}
        return Context(type_resolver=type_map, default_value=None)
