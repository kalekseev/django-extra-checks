from typing import Type, Union

from django.db import models

from .ast import ModelAST
from .exceptions import MissingASTError  # noqa
from .protocols import ArgASTProtocol, FieldASTProtocol, ModelASTProtocol  # noqa


def get_model_ast(
    model_cls: Type[models.Model],
) -> Union[ModelASTProtocol]:
    return ModelAST(model_cls)
