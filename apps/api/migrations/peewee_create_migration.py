import argparse
from importlib import import_module
from inspect import getmembers, isclass
from pathlib import Path

from peewee_migrate.cli import get_router

api_dir = Path(__file__).resolve().parent.parent
src_dir = api_dir / 'src'
migrations_dir = Path(__file__).resolve().parent


def iter_entity_module_names():
    for entities_path in src_dir.rglob('entities.py'):
        module_path = entities_path.relative_to(api_dir).with_suffix('')
        yield '.'.join(module_path.parts)


def load_entity_models():
    model_base = import_module('src.core.entities').Model
    excluded_models = {
        model_base,
        import_module('src.core.entities').Entity,
    }
    models = []

    for entities_module_name in iter_entity_module_names():
        entities_module = import_module(entities_module_name)
        for _, model in getmembers(entities_module, isclass):
            if model.__module__ != entities_module_name:
                continue
            if model in excluded_models or not issubclass(model, model_base):
                continue
            models.append(model)

    return models


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('--database', required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    router = get_router(migrations_dir, args.database, verbose=1)
    router.create(args.name, auto=load_entity_models())


if __name__ == '__main__':
    main()
