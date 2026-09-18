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


# -- Controllers ---------------------------------------------------------------


DOMAIN_EXCEPTIONS = {"ConflictError", "InvalidInputError"}


def _caught_names(handler: ast.ExceptHandler) -> list[str]:
    if handler.type is None:
        return []
    nodes = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    return [
        node.id if isinstance(node, ast.Name) else node.attr
        for node in nodes
        if isinstance(node, (ast.Name, ast.Attribute))
    ]


def test_controllers_must_not_catch_domain_exceptions():
    # The app-level handlers map them; a local catch would drift from that mapping.
    violations = []
    for py in sorted((APP_ROOT / "controllers").rglob("*.py")):
        for node in ast.walk(ast.parse(py.read_text(), filename=str(py))):
            if isinstance(node, ast.ExceptHandler):
                violations += [
                    f"  {py.relative_to(APP_ROOT.parent)}:{node.lineno}: {name}"
                    for name in _caught_names(node)
                    if name in DOMAIN_EXCEPTIONS
                ]
    assert violations == [], (
        "Controllers must not catch domain exceptions:\n" + "\n".join(violations)
    )


# -- Application layer --------------------------------------------------------


def test_application_must_not_import_fastapi():
    violations = [
        (f, m)
        for f, m in _collect_imports(APP_ROOT / "application")
        if m.startswith("fastapi")
    ]
    assert violations == [], "Application layer must not import fastapi:\n" + "\n".join(
        f"  {f}: {m}" for f, m in violations
    )


def test_application_must_not_import_schemas():
    violations = [
        (f, m)
        for f, m in _collect_imports(APP_ROOT / "application")
        if m.startswith("app.controllers.schemas")
    ]
    assert violations == [], "Application layer must not import schemas:\n" + "\n".join(
        f"  {f}: {m}" for f, m in violations
    )


# -- Domain layer --------------------------------------------------------------


def test_application_must_not_import_concrete_repositories():
    """Use cases depend on the ports in `app.domain.repositories`, not on SQLAlchemy.

    The concrete classes live in `app/repositories/` and are wired in the
    controllers. Importing one here would point the dependency outward and make
    the layer untestable without a database — the same reason the password
    hasher is a Protocol in the domain and bcrypt an adapter in infrastructure.
    """
    violations = [
        (f, m)
        for f, m in _collect_imports(APP_ROOT / "application")
        if m.startswith("app.repositories")
    ]
    assert violations == [], (
        "Application layer must depend on app.domain.repositories, "
        "not on concrete repositories:\n"
        + "\n".join(f"  {f}: {m}" for f, m in violations)
    )


def test_domain_must_not_import_upper_layers():
    forbidden = (
        "app.controllers",
        "app.application",
        "app.repositories",
        "app.infrastructure",
    )
    imports = _collect_imports(APP_ROOT / "domain" / "models")

    for extra in (
        APP_ROOT / "domain" / "validators.py",
        APP_ROOT / "domain" / "exceptions.py",
    ):
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
        (f, m) for f, m in imports if any(m.startswith(fb) for fb in forbidden)
    ]
    assert violations == [], (
        "Domain layer must not import from upper layers:\n"
        + "\n".join(f"  {f}: {m}" for f, m in violations)
    )


# -- Repository layer ----------------------------------------------------------


ADAPTER_FORBIDDEN_IMPORTS = ("app.controllers", "app.application", "fastapi")


def test_repositories_must_not_import_controllers_application_or_fastapi():
    violations = [
        (f, m)
        for f, m in _collect_imports(APP_ROOT / "repositories")
        if any(m.startswith(fb) for fb in ADAPTER_FORBIDDEN_IMPORTS)
    ]
    assert violations == [], (
        "Repositories must not import from controllers, application or fastapi:\n"
        + "\n".join(f"  {f}: {m}" for f, m in violations)
    )


# -- Infrastructure layer ------------------------------------------------------


def test_infrastructure_must_not_import_controllers_application_or_fastapi():
    violations = [
        (f, m)
        for f, m in _collect_imports(APP_ROOT / "infrastructure")
        if any(m.startswith(fb) for fb in ADAPTER_FORBIDDEN_IMPORTS)
    ]
    assert violations == [], (
        "Infrastructure must not import from controllers, application or fastapi:\n"
        + "\n".join(f"  {f}: {m}" for f, m in violations)
    )
