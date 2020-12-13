import inspect
import textwrap
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
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


class ModelCST(ModelASTProtocol):
    def __init__(self, model_cls: Type[models.Model]):
        self.model_cls = model_cls
        self._assignments: List[cst.Assign] = []
        self._meta: Optional[cst.ClassDef] = None

    @cached_property
    def _nodes(self) -> Iterator[cst.CSTNode]:
        try:
            source = textwrap.dedent(inspect.getsource(self.model_cls))
        except TypeError:
            # TODO: add warning?
            return iter([])
        return iter(cst.parse_statement(source).body.body)  # type: ignore

    def _parse(self, predicate: Optional[Callable[[cst.CSTNode], bool]] = None) -> None:
        try:
            for node in self._nodes:
                if predicate and predicate(node):
                    self._meta = cast(cst.ClassDef, node)
                    break
                line = (
                    cst.ensure_type(node, cst.SimpleStatementLine)
                    if m.matches(node, m.SimpleStatementLine())
                    else None
                )
                assign = (
                    cst.ensure_type(line.body[0], cst.Assign)
                    if line and m.matches(line.body[0], m.Assign())
                    else None
                )
                if assign:
                    self._assignments.append(assign)
        except StopIteration:
            return
        return

    @cached_property
    def _meta_node(self) -> Optional[cst.ClassDef]:
        if not self._meta:
            self._parse(
                lambda node: m.matches(node, m.ClassDef())
                and cst.ensure_type(node, cst.ClassDef).name.value == "Meta"
            )
        return self._meta

    @cached_property
    def _meta_vars(self) -> Dict[str, cst.Assign]:
        data: Dict[str, cst.Assign] = {}
        if not self._meta_node:
            return data
        for node in self._meta_node.body.body:
            line = (
                cst.ensure_type(node, cst.SimpleStatementLine)
                if m.matches(node, m.SimpleStatementLine())
                else None
            )
            assign = (
                cst.ensure_type(line.body[0], cst.Assign)
                if line and m.matches(line.body[0], m.Assign())
                else None
            )
            name = (
                cst.ensure_type(assign.targets[0].target, cst.Name)
                if assign and m.matches(assign.targets[0].target, m.Name())
                else None
            )
            if name and assign:
                data[name.value] = assign
        return data

    @cached_property
    def field_nodes(self) -> Iterable[Tuple[models.fields.Field, "FieldCST"]]:
        for field in self.model_cls._meta.get_fields(include_parents=False):
            if isinstance(field, models.Field):
                yield field, cast(
                    FieldCST, LazyFieldAST(FieldCST, self.assignments, field)
                )

    @cached_property
    def assignments(self) -> Dict[str, cst.Assign]:
        self._parse()
        result = {}
        for node in self._assignments:
            if m.matches(node.targets[0].target, m.Name()):
                result[cst.ensure_type(node.targets[0].target, cst.Name).value] = node
        return result


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
