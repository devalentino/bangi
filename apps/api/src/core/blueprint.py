from flask_smorest import Blueprint as FlaskSmorestBlueprint
from marshmallow import INCLUDE
from webargs.flaskparser import FlaskParser


class ArgumentsParser(FlaskParser):
    DEFAULT_UNKNOWN_BY_LOCATION = {'query': INCLUDE}


class Blueprint(FlaskSmorestBlueprint):
    ARGUMENTS_PARSER = ArgumentsParser()
