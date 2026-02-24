"""Architecture fitness functions — enforce layer boundaries at test time."""

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent.parent / "app"


def _collect_imports(directory: Path) -> list[tuple[str, str]]:
    """Return [(file_relative, module_name)] for every import in *directory*."""
    results: list[tuple[str, str]] = []
    for py in sorted(directory.rglob("*.py")):
        if py.name == "__init__.py":
            continue
        tree = ast.parse(py.read_text(), filename=str(py))
        rel = str(py.relative_to(APP_ROOT.parent))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    results.append((rel, alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module:
                results.append((rel, node.module))
    return results


# -- Application layer --------------------------------------------------------


def test_application_must_not_import_fastapi():
    violations = [
        (f, m)
        for f, m in _collect_imports(APP_ROOT / "application")
        if m.startswith("fastapi")
    ]
    assert violations == [], (
        "Application layer must not import fastapi:\n"
        + "\n".join(f"  {f}: {m}" for f, m in violations)
    )


def test_application_must_not_import_schemas():
    violations = [
        (f, m)
        for f, m in _collect_imports(APP_ROOT / "application")
        if m.startswith("app.domain.schemas")
    ]
    assert violations == [], (
        "Application layer must not import schemas:\n"
        + "\n".join(f"  {f}: {m}" for f, m in violations)
    )


# -- Domain layer --------------------------------------------------------------


def test_domain_must_not_import_upper_layers():
    forbidden = ("app.controllers", "app.application", "app.repositories", "app.infrastructure")
    imports = _collect_imports(APP_ROOT / "domain" / "models")

    for extra in (APP_ROOT / "domain" / "validators.py", APP_ROOT / "domain" / "exceptions.py"):
        if extra.exists():
            tree = ast.parse(extra.read_text(), filename=str(extra))
            rel = str(extra.relative_to(APP_ROOT.parent))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((rel, alias.name))
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append((rel, node.module))

    violations = [
        (f, m)
        for f, m in imports
        if any(m.startswith(fb) for fb in forbidden)
    ]
    assert violations == [], (
        "Domain layer must not import from upper layers:\n"
        + "\n".join(f"  {f}: {m}" for f, m in violations)
    )


# -- Repository layer ----------------------------------------------------------


def test_repositories_must_not_import_controllers_or_application():
    forbidden = ("app.controllers", "app.application")
    violations = [
        (f, m)
        for f, m in _collect_imports(APP_ROOT / "repositories")
        if any(m.startswith(fb) for fb in forbidden)
    ]
    assert violations == [], (
        "Repositories must not import from controllers or application:\n"
        + "\n".join(f"  {f}: {m}" for f, m in violations)
    )
