import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"


@pytest.mark.parametrize("layer", ["domain", "application", "port", "presentation"])
def test_layer_dependencies(layer):
    forbidden = ("sqlalchemy", "app.adapter")
    if layer != "presentation":
        forbidden += ("fastapi", "starlette", "pydantic", "app.presentation", "app.di")
    if layer == "domain":
        forbidden += ("app.application", "app.port", "app.core")
    for path in (APP / layer).rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            imports = []
            if isinstance(node, ast.Import):
                imports = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports = [node.module]
            for name in imports:
                assert not any(name == dep or name.startswith(dep + ".") for dep in forbidden), (
                    f"{path.relative_to(APP)} imports {name}"
                )
