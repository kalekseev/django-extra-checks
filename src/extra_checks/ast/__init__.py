import importlib
import os
from typing import Type, Union

from django.db import models

from .ast import ModelAST
from .exceptions import MissingASTError  # noqa
from .protocols import ArgASTProtocol, FieldASTProtocol, ModelASTProtocol  # noqa

try:
    from .cst import ModelCST, parse_file
except ImportError:
    pass


class ASTProvider:
    def __init__(self, models):
        self._models = {}
        self._files = {}
        self._visitors = {}
        for model in models:
            file = importlib.import_module(model.__module__).__file__
            self._models[model] = file
            self._files.setdefault(file, set()).add(model)

    def get_ast(self, model_cls):
        if os.environ.get("AST_BACKEND") == "cst":
            return self._get_cst(self, model_cls)
        return ModelAST(model_cls)

    def _get_cst(self, model_cls):
        file = self._models[model_cls]
        if file not in self._visitors:
            self._visitors[file] = parse_file(
                file, {m.__name__ for m in self._files[file]}
            )
        visitor = self._visitors[file]
        return ModelCST(
            model_cls,
            visitor.models[model_cls.__name__]["assignments"],
            visitor.models[model_cls.__name__]["meta_vars"],
        )


def get_model_ast(
    model_cls: Type[models.Model],
) -> Union[ModelASTProtocol]:
    if os.environ.get("AST_BACKEND") == "cst":
        return ModelCST(model_cls)
    return ModelAST(model_cls)
