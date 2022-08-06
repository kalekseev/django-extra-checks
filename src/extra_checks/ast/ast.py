import ast
from functools import partial
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
from django.utils.functional import SimpleLazyObject

from extra_checks.check_id import MODEL_META_CHECKS_NAMES, CheckId

from .exceptions import MissingASTError
from .protocols import (
    ArgASTProtocol,
    DisableCommentProtocol,
    FieldASTProtocol,
    ModelASTProtocol,
)
from .source_provider import SourceProvider

if TYPE_CHECKING:
    cached_property = property
else:
    from django.utils.functional import cached_property


class ModelAST(DisableCommentProtocol, ModelASTProtocol):
    def __init__(self, model_cls: Type[models.Model]):
        self.model_cls = model_cls
        self._assignment_nodes: List[ast.Assign] = []
        self._meta: Optional[ast.ClassDef] = None

    @cached_property
    def _source_provider(self) -> SourceProvider:
        return SourceProvider(self.model_cls)

    @cached_property
    def _nodes(self) -> Iterator[ast.AST]:
        if self._source_provider.source is None:
            return iter([])
        return iter(ast.parse(self._source_provider.source).body[0].body)  # type: ignore

    def _parse(self, predicate: Optional[Callable[[ast.AST], bool]] = None) -> None:
        try:
            for node in self._nodes:
                if predicate and predicate(node):
                    self._meta = cast(ast.ClassDef, node)
                    break
                if isinstance(node, ast.Assign):
                    self._assignment_nodes.append(node)
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
    def _assignments(self) -> Dict[str, ast.Assign]:
        self._parse()
        result = {}
        for node in self._assignment_nodes:
            if isinstance(node.targets[0], ast.Name):
                result[node.targets[0].id] = node
        return result

    @cached_property
    def field_nodes(self) -> Iterable[Tuple[models.fields.Field, "FieldAST"]]:
        for field in self.model_cls._meta.get_fields(include_parents=False):
            if isinstance(field, models.Field):
                yield field, cast(
                    FieldAST, SimpleLazyObject(partial(get_field_ast, self, field))
                )

    def has_meta_var(self, name: str) -> bool:
        return name in self._meta_vars

    def is_disabled_by_comment(self, check_id: str) -> bool:
        check = CheckId.find_check(check_id)
        if check in MODEL_META_CHECKS_NAMES:
            if not self._meta_node:
                # class Meta is not defined on model
                return False
            return check in self._source_provider.get_disabled_checks_for_line(
                self._meta_node.lineno
            )
        return check in self._source_provider.get_disabled_checks_for_line(1)


def get_field_ast(model_ast: ModelAST, field: models.Field) -> "FieldAST":
    try:
        return FieldAST(
            model_ast._assignments[field.name], field, model_ast._source_provider
        )
    except KeyError:
        raise MissingASTError()


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


class FieldAST(DisableCommentProtocol, FieldASTProtocol):
    def __init__(
        self, node: ast.Assign, field: models.Field, source_provider: SourceProvider
    ):
        self._node = node
        self._field = field
        self._source_provider = source_provider

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

    def is_disabled_by_comment(self, check_id: str) -> bool:
        return CheckId.find_check(
            check_id
        ) in self._source_provider.get_disabled_checks_for_line(self._node.lineno)
