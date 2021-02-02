import functools
import operator
from typing import (
    TYPE_CHECKING,
    Dict,
    Iterable,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

import libcst as cst
from django.db import models
from libcst import matchers as m

from .lazy import LazyFieldAST
from .protocols import ArgASTProtocol, FieldASTProtocol, ModelASTProtocol

if TYPE_CHECKING:
    cached_property = property
else:
    from django.utils.functional import cached_property


def parse_file(file, model_names):
    _names = [name for name in model_names]
    names = functools.reduce(operator.or_, [m.Name(name) for name in model_names])

    class Collector(m.MatcherDecoratableVisitor):
        def __init__(self):
            self.models = {}
            self.current = None
            super().__init__()

        def visit_FunctionDef(self, node: cst.FunctionDef):
            return False

        @m.visit(m.ClassDef(names))
        def visit_model(self, node: cst.ClassDef):
            if node.name.value not in self.models:
                self.models[node.name.value] = {"assignments": {}, "meta_vars": {}}
            self.current = self.models[node.name.value]
            return True

        @m.leave(m.ClassDef(names))
        def leave_model(self, node: cst.ClassDef):
            self.current = None

        @m.call_if_inside(m.ClassDef(names))
        def visit_ClassDef(self, node: cst.FunctionDef):
            return node.name.value in {*_names, "Meta"}

        @m.call_if_inside(m.ClassDef(names))
        @m.call_if_not_inside(m.ClassDef(m.Name("Meta")))
        @m.visit(m.Assign(value=m.Call()))
        def fields(self, node: cst.Assign):
            self.current["assignments"][node.targets[0].target.value] = node

        @m.call_if_inside(m.ClassDef(names))
        @m.call_if_inside(m.ClassDef(m.Name("Meta")))
        @m.visit(m.Assign())
        def meta_vars(self, node: cst.Assign):
            self.current["meta_vars"][node.targets[0].target.value] = node

    visitor = Collector()
    tree = cst.parse_module(open(file).read())
    tree.visit(visitor)
    return visitor


class ModelCST(ModelASTProtocol):
    def __init__(self, model_cls: Type[models.Model], assignments, meta_vars):
        self.model_cls = model_cls
        self._assignments = assignments
        self._meta_vars = meta_vars

    @cached_property
    def field_nodes(self) -> Iterable[Tuple[models.fields.Field, "FieldCST"]]:
        for field in self.model_cls._meta.get_fields(include_parents=False):
            if isinstance(field, models.Field):
                yield field, cast(
                    FieldCST, LazyFieldAST(FieldCST, self._assignments, field)
                )

    def has_meta_var(self, name: str) -> bool:
        return name in self._meta_vars


class FieldCST(FieldASTProtocol):
    def __init__(self, node: cst.Assign, field: models.Field):
        self._node = node
        self._field = field

    @cached_property
    def _args(self) -> Sequence[cst.Arg]:
        if m.matches(self._node.value, m.Call()):
            return cst.ensure_type(self._node.value, cst.Call).args
        raise ValueError("Not a field assignment")

    @cached_property
    def _kwargs(self) -> Dict[str, cst.Arg]:
        if m.matches(self._node.value, m.Call()):
            return {
                kw.keyword.value: kw
                for kw in cst.ensure_type(self._node.value, cst.Call).args
                if kw.keyword
            }
        raise ValueError("Not a field assignment")

    @cached_property
    def _verbose_name(self) -> Union[None, cst.BaseString, cst.Call]:
        result = getattr(
            getattr(self._kwargs.get("verbose_name"), "value", None), "value", None
        )
        if result:
            return result
        if isinstance(self._field, models.fields.related.RelatedField):
            return None
        if self._args:
            node = self._args[0].value
            call = (
                cst.ensure_type(node, cst.Call) if m.matches(node, m.Call()) else None
            )
            if call and not m.matches(call.func, m.Attribute()):
                return call
            elif m.matches(node, m.SimpleString()):
                return cst.ensure_type(node, cst.SimpleString)
        return None

    def get_arg(self, name: str) -> Optional[ArgASTProtocol]:
        if name == "verbose_name":
            return ArgCST(self._verbose_name) if self._verbose_name else None
        return ArgCST(self._kwargs[name].value) if name in self._kwargs else None


class ArgCST(ArgASTProtocol):
    def __init__(self, node: cst.CSTNode) -> None:
        self._node = node

    @property
    def callable_func_name(self) -> Optional[str]:
        return (
            cst.ensure_type(self._node, cst.Call).func.value  # type: ignore
            if self.is_callable
            else None
        )

    def get_call_first_args(self) -> str:
        return self._node.args[0].value.value  # type: ignore

    @cached_property
    def is_callable(self) -> bool:
        return m.matches(self._node, m.Call())
