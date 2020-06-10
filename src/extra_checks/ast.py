import ast
import inspect
from typing import (
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

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils.functional import cached_property


class ModelAST:
    def __init__(self, model_cls: Type[models.Model]):
        self.model_cls = model_cls
        self._assignments: List[ast.Assign] = []
        self._meta: Optional[ast.ClassDef] = None

    @property
    def is_abstract(self) -> bool:
        return self.model_cls._meta.abstract

    @property
    def is_proxy(self) -> bool:
        return self.model_cls._meta.proxy

    @cached_property
    def _nodes(self) -> Iterator[ast.AST]:
        source = inspect.getsource(self.model_cls)
        return iter(ast.parse(source).body[0].body)  # type: ignore

    def _parse(self, predicate: Callable[[ast.AST], bool] = None) -> None:
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
    def meta_node(self) -> Optional[ast.ClassDef]:
        if not self._meta:
            self._parse(
                lambda node: isinstance(node, ast.ClassDef) and node.name == "Meta"
            )
        return self._meta

    @cached_property
    def meta_vars(self) -> Dict[str, ast.Assign]:
        data: Dict[str, ast.Assign] = {}
        if not self.meta_node:
            return data
        for node in ast.iter_child_nodes(self.meta_node):
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                data[node.targets[0].id] = node
        return data

    @cached_property
    def field_nodes(self) -> Iterable[Tuple[models.fields.Field, ast.Assign]]:
        self._parse()
        for node in self._assignments:
            if isinstance(node.targets[0], ast.Name):
                field_name = node.targets[0].id
                try:
                    field = self.model_cls._meta.get_field(field_name)
                except FieldDoesNotExist:
                    pass
                else:
                    yield field, node


class _CallType(ast.Call):
    func: Union[ast.Attribute, ast.Name]


class _AssignType(ast.Assign):
    value: _CallType


class FieldAST:
    def __init__(self, node: ast.Assign):
        self._node = cast(_AssignType, node)
        self._args = self._node.value.args

    @cached_property
    def field_class_name(self) -> str:
        if isinstance(self._node.value.func, ast.Name):
            return self._node.value.func.id
        else:
            return self._node.value.func.attr

    @cached_property
    def args(self) -> List[ast.expr]:
        return self._node.value.args

    @cached_property
    def kwargs(self) -> Dict[str, ast.keyword]:
        return {kw.arg: kw for kw in self._node.value.keywords if kw.arg}

    @cached_property
    def verbose_name(self) -> Union[None, ast.Constant, ast.Call]:
        result = getattr(self.kwargs.get("verbose_name"), "value", None)
        if result:
            return result
        if (
            self.field_class_name
            not in ("OneToOneField", "ManyToManyField", "ForeignKey")
            and self.args
        ):
            node = self.args[0]
            if isinstance(node, ast.Call) and hasattr(node.func, "id"):
                return node
        return None

    @cached_property
    def help_text(self) -> Optional[ast.AST]:
        return getattr(self.kwargs.get("help_text"), "value", None)
