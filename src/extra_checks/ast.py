import ast
import inspect
import textwrap
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

import libcst as cst
from django.db import models
from django.utils.functional import cached_property
from libcst import matchers as m

from .exceptions import MissingASTError

if TYPE_CHECKING:

    class _CallType(ast.Call):
        func: Union[ast.Attribute, ast.Name]

    class _AssignType(ast.Assign):
        value: _CallType


class ModelCST:
    def __init__(self, model_cls: Type[models.Model]):
        self.model_cls = model_cls
        self._assignments: List[ast.Assign] = []
        self._meta: Optional[ast.ClassDef] = None

    @cached_property
    def _nodes(self) -> Iterator[ast.AST]:
        try:
            source = textwrap.dedent(inspect.getsource(self.model_cls))
        except TypeError:
            # TODO: add warning?
            return iter([])
        return iter(cst.parse_statement(source).body.body)  # type: ignore

    def _parse(self, predicate: Optional[Callable[[ast.AST], bool]] = None) -> None:
        try:
            for node in self._nodes:
                if predicate and predicate(node):
                    self._meta = cast(cst.ClassDef, node)
                    break
                if m.matches(node, m.SimpleStatementLine()) and m.matches(
                    node.body[0], m.Assign()
                ):
                    self._assignments.append(node.body[0])
        except StopIteration:
            return
        return

    @cached_property
    def _meta_node(self) -> Optional[ast.ClassDef]:
        if not self._meta:
            self._parse(
                lambda node: m.matches(node, m.ClassDef()) and node.name.value == "Meta"
            )
        return self._meta

    @cached_property
    def meta_vars(self) -> Dict[str, ast.Assign]:
        data: Dict[str, ast.Assign] = {}
        if not self._meta_node:
            return data
        for node in self._meta_node.body.body:
            if m.matches(node.body[0], m.Assign()) and m.matches(
                node.body[0].targets[0].target, m.Name()
            ):
                data[node.body[0].targets[0].target.value] = node.body[0]
        return data

    @cached_property
    def field_nodes(self) -> Iterable[Tuple[models.fields.Field, "FieldAST"]]:
        for field in self.model_cls._meta.get_fields(include_parents=False):
            if isinstance(field, models.Field):
                yield field, cast(FieldAST, LazyFieldAST(self, field))

    @cached_property
    def assignments(self) -> Dict[str, ast.Assign]:
        self._parse()
        result = {}
        for node in self._assignments:
            if m.matches(node.targets[0].target, m.Name()):
                result[node.targets[0].target.value] = node
        return result


class ModelAST:
    def __init__(self, model_cls: Type[models.Model]):
        self.model_cls = model_cls
        self._assignments: List[ast.Assign] = []
        self._meta: Optional[ast.ClassDef] = None

    @cached_property
    def _nodes(self) -> Iterator[ast.AST]:
        try:
            source = textwrap.dedent(inspect.getsource(self.model_cls))
        except TypeError:
            # TODO: add warning?
            return iter([])
        return iter(ast.parse(source).body[0].body)  # type: ignore

    def _parse(self, predicate: Optional[Callable[[ast.AST], bool]] = None) -> None:
        try:
            for node in self._nodes:
                if predicate and predicate(node):
                    self._meta = cast(ast.ClassDef, node)
                    break
                if isinstance(node, ast.Assign):
                    self._assignments.append(node)
        except StopIteration:
            return
        return

    @cached_property
    def _meta_node(self) -> Optional[ast.ClassDef]:
        if not self._meta:
            self._parse(
                lambda node: isinstance(node, ast.ClassDef) and node.name == "Meta"
            )
        return self._meta

    @cached_property
    def meta_vars(self) -> Dict[str, ast.Assign]:
        data: Dict[str, ast.Assign] = {}
        if not self._meta_node:
            return data
        for node in ast.iter_child_nodes(self._meta_node):
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                data[node.targets[0].id] = node
        return data

    @cached_property
    def field_nodes(self) -> Iterable[Tuple[models.fields.Field, "FieldAST"]]:
        for field in self.model_cls._meta.get_fields(include_parents=False):
            if isinstance(field, models.Field):
                yield field, cast(FieldAST, LazyFieldAST(self, field))

    @cached_property
    def assignments(self) -> Dict[str, ast.Assign]:
        self._parse()
        result = {}
        for node in self._assignments:
            if isinstance(node.targets[0], ast.Name):
                result[node.targets[0].id] = node
        return result


class LazyFieldAST:
    def __init__(self, model_ast: ModelAST, field: models.Field) -> None:
        self.model_ast = model_ast
        self.field = field
        self.field_ast: Optional[FieldAST] = None

    def __getattr__(self, name: str) -> Any:
        if not self.field_ast:
            try:
                self.field_ast = FieldCST(
                    self.model_ast.assignments[self.field.name], self.field
                )
            except KeyError:
                raise MissingASTError()
        return getattr(self.field_ast, name)


class FieldAST:
    def __init__(self, node: ast.Assign, field: models.Field):
        self._node = cast("_AssignType", node)
        self._args = self._node.value.args
        self._field = field

    @cached_property
    def _args(self) -> List[ast.expr]:
        return self._node.value.args

    @cached_property
    def _kwargs(self) -> Dict[str, ast.keyword]:
        return {kw.arg: kw for kw in self._node.value.keywords if kw.arg}

    @cached_property
    def help_text(self) -> Optional[ast.AST]:
        return getattr(self._kwargs.get("help_text"), "value", None)

    @cached_property
    def verbose_name(self) -> Union[None, ast.Constant, ast.Call]:
        result = getattr(self._kwargs.get("verbose_name"), "value", None)
        if result:
            return result
        if isinstance(self._field, models.fields.related.RelatedField):
            return None
        if self._args:
            node = self._args[0]
            if isinstance(node, ast.Call) and hasattr(node.func, "id"):
                return node
            elif isinstance(node, (ast.Constant, ast.Str)):
                return node
        return None

    @classmethod
    def is_gettext_node(cls, node: ast.AST, gettext_func: str) -> bool:
        return (
            isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == gettext_func
        )

    @classmethod
    def get_call_value(cls, node: ast.Call) -> str:
        return node.args[0].s  # type: ignore

    def has_kwarg(self, name: str) -> bool:
        return name in self._kwargs


class FieldCST:
    def __init__(self, node: ast.Assign, field: models.Field):
        self._node = cast("_AssignType", node)
        self._args = self._node.value.args
        self._field = field

    @cached_property
    def _args(self) -> List[ast.expr]:
        return [a for a in self._node.value.args if a.keyword is None]

    @cached_property
    def _kwargs(self) -> Dict[str, ast.keyword]:
        return {kw.keyword.value: kw for kw in self._node.value.args if kw.keyword}

    @cached_property
    def help_text(self) -> Optional[ast.AST]:
        return getattr(
            getattr(self._kwargs.get("help_text"), "value", None), "value", None
        )

    @cached_property
    def verbose_name(self) -> Union[None, ast.Constant, ast.Call]:
        result = getattr(
            getattr(self._kwargs.get("verbose_name"), "value", None), "value", None
        )
        if result:
            return result
        if isinstance(self._field, models.fields.related.RelatedField):
            return None
        if self._args:
            node = self._args[0].value
            if m.matches(node, m.Call()) and not m.matches(node.func, m.Attribute()):
                return node
            elif m.matches(node, m.SimpleString()):
                return node.value
        return None

    @staticmethod
    def is_gettext_node(node: ast.AST, gettext_func: str) -> bool:
        return (
            m.matches(node, m.Call())
            and getattr(node.func, "value", None) == gettext_func
        )

    def has_kwarg(self, name):
        return name in self._kwargs
