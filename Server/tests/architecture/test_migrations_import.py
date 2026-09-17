import importlib.util
from pathlib import Path

import pytest

VERSIONS_DIR = Path(__file__).resolve().parents[2] / "alembic" / "versions"
MIGRATIONS = sorted(VERSIONS_DIR.glob("*.py"))


def test_migrations_directory_is_not_empty():
    assert MIGRATIONS


@pytest.mark.parametrize("path", MIGRATIONS, ids=lambda p: p.stem)
def test_migration_module_imports(path):
    # Tests build the schema with `metadata.create_all`, so migrations never run
    # here. Importing them at least catches a removed dependency (e.g. passlib)
    # before `alembic upgrade` breaks on a fresh database.
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.upgrade)
    assert callable(module.downgrade)
