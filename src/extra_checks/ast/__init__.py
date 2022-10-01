from typing import Container, Type

from django.db import models

from ..check_id import CheckId
from .ast import ModelAST
from .exceptions import MissingASTError
from .protocols import (
    ArgASTProtocol,
    FieldASTProtocol,
    ModelASTDisableCommentProtocol,
    ModelASTProtocol,
)


def get_model_ast(
    model_cls: Type[models.Model],
    meta_checks: Container[CheckId],
) -> ModelASTDisableCommentProtocol:
    return ModelAST(model_cls, meta_checks)


__all__ = [
    "get_model_ast",
    "MissingASTError",
    "ArgASTProtocol",
    "FieldASTProtocol",
    "ModelASTProtocol",
]
