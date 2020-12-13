import os
from typing import Type, Union

from django.db import models

from .ast import ModelAST
from .exceptions import MissingASTError  # noqa
from .protocols import ArgASTProtocol, FieldASTProtocol, ModelASTProtocol  # noqa

try:
    from .cst import ModelCST
except ImportError:
    pass


def get_model_ast(
    model_cls: Type[models.Model],
) -> Union[ModelASTProtocol]:
    if os.environ.get("AST_BACKEND") == "cst":
        return ModelCST(model_cls)
    return ModelAST(model_cls)
