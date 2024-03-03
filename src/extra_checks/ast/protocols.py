from typing import Any, Iterable, Optional, Protocol, Tuple

from django.db import models


class ArgASTProtocol(Protocol):
    @property
    def is_callable(self) -> bool: ...

    @property
    def callable_func_name(self) -> Optional[str]: ...

    def get_call_first_args(self) -> Any: ...


class FieldASTProtocol(Protocol):
    def get_arg(self, name: str) -> Optional[ArgASTProtocol]: ...


class ModelASTProtocol(Protocol):
    @property
    def field_nodes(
        self,
    ) -> Iterable[Tuple[models.fields.Field, "FieldASTDisableCommentProtocol"]]: ...

    def has_meta_var(self, name: str) -> bool: ...


class DisableCommentProtocol(Protocol):
    def is_disabled_by_comment(self, check_id: str) -> bool: ...


class ModelASTDisableCommentProtocol(
    ModelASTProtocol, DisableCommentProtocol, Protocol
): ...


class FieldASTDisableCommentProtocol(
    FieldASTProtocol, DisableCommentProtocol, Protocol
): ...
