import ast
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
    Tuple,
    Type,
    Union,
    cast,
)

from django.db import models

from .lazy import LazyFieldAST
from .protocols import ArgASTProtocol, FieldASTProtocol, ModelASTProtocol

if TYPE_CHECKING:
    cached_property = property
else:
    from django.utils.functional import cached_property


class ModelAST(ModelASTProtocol):
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
    def _meta_vars(self) -> Dict[str, ast.Assign]:
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
                yield field, cast(
                    FieldAST, LazyFieldAST(FieldAST, self.assignments, field)
                )

    @cached_property
    def assignments(self) -> Dict[str, ast.Assign]:
        self._parse()
        result = {}
        for node in self._assignments:
            if isinstance(node.targets[0], ast.Name):
                result[node.targets[0].id] = node
        return result


class ArgAST(ArgASTProtocol):
    def __init__(self, node: ast.AST):
        self._node = node

    @cached_property
    def is_callable(self) -> bool:
        return isinstance(self._node, ast.Call)

    @cached_property
    def callable_func_name(self) -> Optional[str]:
        return (
            getattr(self._node.func, "id", None)
            if isinstance(self._node, ast.Call)
            else None
        )

    def get_call_first_args(self) -> str:
        return self._node.args[0].s  # type: ignore


class FieldAST(FieldASTProtocol):
    def __init__(self, node: ast.Assign, field: models.Field):
        self._node = node
        self._field = field

    @cached_property
    def _args(self) -> List[ast.expr]:
        return self._node.value.args  # type: ignore

    @cached_property
    def _kwargs(self) -> Dict[str, ast.keyword]:
        return {kw.arg: kw for kw in self._node.value.keywords if kw.arg}  # type: ignore

    def get_arg(self, name: str) -> Optional[ArgASTProtocol]:
        if name == "verbose_name":
            return ArgAST(self._verbose_name) if self._verbose_name else None
        return ArgAST(self._kwargs[name].value) if name in self._kwargs else None

    @cached_property
    def _verbose_name(self) -> Union[None, ast.Constant, ast.Call]:
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