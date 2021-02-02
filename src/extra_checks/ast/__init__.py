from typing import Type, Union

from django.db import models

from .ast import ModelAST
from .exceptions import MissingASTError
from .protocols import ArgASTProtocol, FieldASTProtocol, ModelASTProtocol


def get_model_ast(
    model_cls: Type[models.Model],
) -> Union[ModelASTProtocol]:
    return ModelAST(model_cls)


__all__ = [
    "get_model_ast",
    "MissingASTError",
    "ArgASTProtocol",
    "FieldASTProtocol",
    "ModelASTProtocol",
]
